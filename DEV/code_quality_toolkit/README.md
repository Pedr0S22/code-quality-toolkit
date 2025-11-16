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

## Plugins incluídos

O Code Quality Toolkit já inclui dois plugins de análise de código: complexity e dead_code.
Ambos seguem o contrato definido em plugins/base.py e são descobertos automaticamente via loader.discover_plugins().

### Plugin complexity — Cyclomatic Complexity

Este plugin calcula a complexidade ciclomática de cada função e método presente nos ficheiros analisados.
A métrica segue o modelo clássico de McCabe, incrementando a complexidade em pontos de decisão, tais como:

instruções de controlo (if, elif, else);

ciclos (for, while);

blocos de exceção (try, except);

operadores booleanos (and, or);

compreensões com condições ([x for ... if cond]).

A complexidade calculada é comparada com o limiar configurado em toolkit.toml:

[rules]
max_complexity = 10


#### Comportamento do plugin:

Para cada função/método cuja complexidade seja superior ao limiar definido, o plugin emite uma issue com:

plugin: "complexity"

code: "HIGH_COMPLEXITY"

severity: "medium" ou "high"

line: linha de definição da função

message: explicação da complexidade calculada e sugestão de refatoração

#### Erros de sintaxe:

Se ocorrer um SyntaxError ao analisar o ficheiro:

é emitida uma issue com code = "SYNTAX_ERROR"

o estado do plugin para esse ficheiro é marcado como partial

### Plugin dead_code — Detecção de código não utilizado

Este plugin identifica código potencialmente morto — símbolos definidos mas nunca utilizados.
Pode detetar:

funções definidas mas nunca chamadas;

imports não utilizados;

variáveis atribuídas mas nunca lidas;

símbolos ignorados por padrão conforme configuração.

A configuração pode incluir regras opcionais:

[rules.dead_code]
ignore_paths = ["tests/**", "*/migrations/**"]


#### Comportamento do plugin:

Para cada símbolo considerado “morto”, o plugin gera uma issue com:

plugin: "dead_code"

code: "UNUSED_FUNCTION" ou "UNUSED_IMPORT", entre outros

severity: "low" ou "medium"

line: posição exata da definição

message: sugestão para remoção ou justificativa

### Aparição no report.json

Todas as issues geradas pelos plugins surgem no relatório final, organizadas por:

ficheiro

plugin

severidade

localização

mensagem e código

O pipeline de agregação (aggregate()) inclui estas issues nas métricas globais, garantindo que validate_unified_report() mantém o formato esperado.

## Documentação adicional

- [`web/SPEC.md`](web/SPEC.md): proposta de interface Web que consome o
  `report.json`.

## Licença

Distribuído sob licença MIT. Consulte `LICENSE` para detalhes.

