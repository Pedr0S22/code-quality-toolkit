# Code Quality Toolkit

O Code Quality Toolkit é um MVP de um motor de análise baseado em plugins, capaz de produzir relatórios de qualidade de código unificados em JSON e consumidos por uma CLI e uma Web UI leve.

## Instalação rápida

```bash
make setup
```

Este comando cria um ambiente virtual `.venv` e instala as dependências.

## Como executar uma análise

```bash
make run
```

ou diretamente com a CLI:

```bash
python -m toolkit.core.cli analyze examples/sample_project --out report.json
```
Para um guia detalhado sobre todas as opções e como interpretar os resultados, consulte o ficheiro HOWTO.md.

### Opções da CLI

1. Ao usar o comando
```bash
make run
```
utilizar um dos argumentos (optional):

```
make run arg=
  "--plugins all | StyleChecker,CyclomaticComplexity"
  "--out report.json"
  "--include-glob "**/*.py" (repetível)"
  "--exclude-glob "tests/**" (repetível)"
  "--config toolkit.toml"
  "--fail-on-severity low|medium|high"
  "--log-level DEBUG|INFO|WARNING|ERROR"
  "-v | --verbose"
```

2. Usando o CLI com: 

```bash
python -m toolkit.core.cli analyze examples/sample_project --out report.json
```
utilizar um dos argumentos (optional):
```
toolkit analyze <path>
  --plugins all | StyleChecker,CyclomaticComplexity
  --out report.json
  --include-glob "**/*.py" (repetível)
  --exclude-glob "tests/**" (repetível)
  --config toolkit.toml
  --fail-on-severity low|medium|high
  --log-level DEBUG|INFO|WARNING|ERROR
  -v | --verbose
```

Exit codes:

- `0` análise concluída e sem violações acima do limiar configurado;
- `1` erro de execução (ex.: falha ao carregar plugin);
- `2` severidade encontrada igual ou superior ao limiar definido.

## Estrutura

```
src/toolkit/
  core/        # infraestrutura do motor e CLI
  plugins/     # plugins descobertos dinamicamente
  utils/       # utilitários partilhados (config, fs)
```

Os relatórios são gravados como `report.json`, contendo um resumo global e
resultados detalhados por ficheiro e plugin.

## Descoberta e ciclo de vida dos plugins

1. **Descoberta:** `toolkit.core.loader.discover_plugins()` percorre dinamicamente o diretório `src/toolkit/plugins` através de `_iter_plugin_modules()` e identifica cada subpasta que contenha um `plugin.py`.
2. **Carregamento:** `toolkit.core.loader.load_plugins()` importa os módulos com `_import_module_from_path()`, instância a classe `Plugin` exposta por cada módulo e valida o contrato via `_validate_metadata()`. O contrato básico exigido está documentado em `toolkit.plugins.base.BasePlugin`.
3. **Execução:** `toolkit.core.engine.run_analysis()` recebe o mapa de instâncias carregadas, configura cada plugin (caso exponha `configure`) e executa `analyze()` para cada ficheiro descoberto por `toolkit.utils.fs.discover_files()`. Exceções são transformadas em relatórios estruturados, registando o estado `partial` em `plugin_status`.
4. **Agregação:** `toolkit.core.aggregator.aggregate()` consolida os relatórios por ficheiro e o estado final de cada plugin, calcula métricas (por severidade, por plugin, top offenders) e valida a estrutura final com `validate_unified_report()`.
5. **Integração na CLI:** `toolkit.core.cli._run_analyze()` orquestra o fluxo chamando `load_plugins()`, `run_analysis()` e `aggregate()`, produzindo o `report.json` com data, versão da ferramenta e estatísticas de execução.

## Arquitetura de Tratamento de Erros
O sistema foi desenhado com uma arquitetura de resiliência robusta, assegurando que a falha individual de qualquer plugin não comprometa a conclusão da análise do projeto.

### 1. Camada da Interface de Linha de Comandos (CLI - `cli.py`)

A CLI funciona como a principal linha de defesa externa para o sistema:
  * **Gestão de Erros Previstos:** Captura e trata exceções operacionais esperadas (`ConfigurationError`, `PluginLoadError`, `AnalysisExecutionError`), terminando a execução com o código de saída `1`.
  * **Gestão de Erros Imprevistos (Crashes):** Inclui um bloco `except Exception` genérico para intercetar falhas inesperadas. Estes erros são registados detalhadamente antes do sistema terminar com o código de saída `2`.

### 2. Camada do Motor de Análise (`engine.py`)

A lógica principal de resiliência reside no motor, especificamente na função `run_analysis`, que garante o isolamento da execução:

**Isolamento e Continuidade dos Plugins:**

* A execução de cada plugin é encapsulada num bloco `try...except`.
* **Em caso de acontecer o except no `analyze()`:**
    * O erro é capturado e registado (etiqueta `plugin.failure`).
    * O plugin que falhou é assinalado como `"partial"` no relatório final.
    * É gerado um relatório de erro sintético no JSON de saída com nível de severidade `high` e o código `PLUGIN_ERROR`.
* **Continuidade:** O motor ignora a falha do plugin e prossegue com a execução dos plugins que faltam e o processamento de outros ficheiros. Isto garante que o utilizador receba um relatório parcial útil, em vez de uma falha completa e vazia.

## Criar um novo plugin

1. Crie um diretório em `src/toolkit/plugins/<nome_do_plugin>` com um ficheiro
   `plugin.py`.
2. Implemente uma classe ou objeto com as funções `get_metadata()` e
   `analyze(source_code: str, file_path: str | None)` seguindo o contrato em
   `plugins/base.py`.
3. Registe qualquer configuração necessária em `toolkit.toml`.
4. Utilize `# EXTENSION-POINT:` para documentar pontos de expansão.

Teste o plugin com `pytest` e execute a CLI para gerar relatórios que o incluam.

## Documentação adicional

- [`web/SPEC.md`](web/SPEC.md): proposta de interface Web que consome o
  `report.json`.

## Licença

Distribuído sob licença MIT. Consulte `LICENSE` para detalhes.
