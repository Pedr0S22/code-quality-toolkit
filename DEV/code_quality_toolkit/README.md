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

## Plugins incluídos

O Code Quality Toolkit inclui dois plugins principais: **Cyclomatic Complexity** e **Dead Code Detector**.  
Ambos seguem o contrato definido em `plugins/base.py`, são carregados automaticamente pelo motor e suportam configuração via `toolkit.toml`.

---

#  Cyclomatic Complexity Plugin

O plugin **Cyclomatic Complexity** avalia a complexidade de funções e métodos, seguindo o modelo clássico de McCabe.  
Além disso, implementa duas métricas adicionais requeridas no issue: **tamanho da função** e **número de argumentos**.

---

##  User Documentation

###  O que este plugin analisa
O plugin produz três tipos de verificações:

1. **Cyclomatic Complexity**  
   - Incrementa a complexidade para cada ponto de decisão (`if`, `elif`, `while`, `for`, `and`, `or`, `except`, compreensões condicionais).  
   - Funções acima do limite configurado são sinalizadas com:  
     **`HIGH_COMPLEXITY`**

2. **Function Length**  
   - Mede o número de linhas reais de cada função.  
   - Funções maiores que o valor configurado são marcadas como:  
     **`LONG_FUNCTION`**

3. **Argument Count**  
   - Conta os argumentos definidos pela função.  
   - Funções que excedem o limite são marcadas como:  
     **`TOO_MANY_ARGUMENTS`**

---

##  Configuração em `toolkit.toml`

O comportamento deste plugin é controlado pela secção:

```toml
[rules.complexity]
max_complexity = 10
max_function_length = 50
max_arguments = 5
```

O utilizador pode ajustar estes valores para tornar a análise mais ou menos permissiva.  
O plugin é carregado automaticamente pelo motor de análise.

---

##  Como executar

```bash
python -m toolkit.core.cli analyze <path> --out report.json
# ou
make run
```

---

##  Porque é importante usar este plugin?

Funções demasiado complexas tornam-se difíceis de testar, modificar e manter.  
Funções demasiado longas acumulam responsabilidades, violando princípios de design.  
Um número elevado de argumentos aumenta o acoplamento e reduz a legibilidade.

Este plugin permite detetar automaticamente estes problemas, ajudando o utilizador a melhorar a qualidade do código.

---
##  Developer Documentation

Internamente, o plugin:

- estende o contrato definido em `BasePlugin`;  
- analisa o AST de cada ficheiro Python;  
- soma pontos de decisão para calcular a complexidade ciclomática;  
- mede a extensão do corpo da função;  
- recolhe o número de argumentos formais;  
- devolve issues estruturadas no formato esperado pelo motor.

Todos os erros de sintaxe são convertidos em issues com o código:  
**`SYNTAX_ERROR`**,  
e o estado do plugin para esse ficheiro passa a **partial** (comportamento padrão do engine).

---


 

## Licença

Distribuído sob licença MIT. Consulte `LICENSE` para detalhes.
