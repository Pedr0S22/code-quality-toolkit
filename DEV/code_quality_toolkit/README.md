# Code Quality Toolkit

O Code Quality Toolkit é um MVP de um
motor de análise baseado em plugins, capaz de produzir relatórios de qualidade de código unificados em
JSON e consumidos por uma CLI e uma Web UI leve.

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

## Criar um novo plugin

1. Crie um diretório em `src/toolkit/plugins/<nome_do_plugin>` com um ficheiro
   `plugin.py`.
2. Implemente uma classe ou objeto com as funções `get_metadata()` e
   `analyze(source_code: str, file_path: str | None)` seguindo o contrato em
   `plugins/base.py`.
3. Registe qualquer configuração necessária em `toolkit.toml`.
4. Utilize `# EXTENSION-POINT:` para documentar pontos de expansão.

Teste o plugin com `pytest` e execute a CLI para gerar relatórios que o incluam.

#  Dead Code Detector Plugin

O plugin **Dead Code Detector** identifica elementos definidos mas nunca utilizados, ajudando a eliminar código redundante e melhorar a manutenibilidade.

---

##  User Documentation

###  O que este plugin deteta
- Funções nunca chamadas  
- Classes não utilizadas  
- Variáveis atribuídas mas nunca lidas  
- Imports não utilizados  
- Elementos ignoráveis via configuração (nomes curtos, padrões a ignorar, dunders)

---

##  Configuração em `toolkit.toml`

```toml
[rules.dead_code]
ignore_patterns = ["tests/**", "*/migrations/**"]
min_name_len = 3
severity = "low"
```

O utilizador pode ajustar:

- `ignore_patterns` → padrões que devem ser sempre ignorados  
- `min_name_len` → nomes demasiado curtos são considerados irrelevantes  
- `severity` → nível associado às issues detetadas

---

##  Como executar

```bash
python -m toolkit.core.cli analyze <path> --out report.json
# ou
make run
```

---

##  Porque é importante usar este plugin?

Código morto dificulta a leitura do projeto, aumenta o tamanho da base de código e gera confusão entre componentes ativos e obsoletos.  
Este plugin ajuda a manter o projeto limpo, claro e mais fácil de manter ao longo do tempo.

---

##  Developer Documentation

O plugin utiliza um visitante de AST (`_DefUseVisitor`) para recolher:

- definições de funções, classes, variáveis e imports;  
- localizações de todas as utilizações destes símbolos;  
- símbolos nunca utilizados dentro do mesmo ficheiro.

Após a análise, o plugin emite issues como:

- **`UNUSED_FUNCTION`**  
- **`UNUSED_CLASS`**  
- **`UNUSED_IMPORT`**  
- **`DEAD_CODE`**

Cada issue contém: `plugin`, `code`, `line`, `severity` e `message`.

A integração e estrutura seguem rigorosamente o contrato do Toolkit.

## Documentação adicional

- [`web/SPEC.md`](web/SPEC.md): proposta de interface Web que consome o
  `report.json`.

## Licença

Distribuído sob licença MIT. Consulte `LICENSE` para detalhes.
