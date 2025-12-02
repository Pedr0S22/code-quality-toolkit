Membros:

João Neto  2023234004  @Imajellyfish  
João Eduardo Duarte  2011187848  @jeduarteldm  
Bernardo Fonseca  2021239253  @jF202  
Diogo Delvivo  2021150174  @delvivo.diogo1  
Catarina Vieira 2023218473  @27634982


Como usar e configurar o sistema de relatórios

1. Visão Geral do Uso
O Core Unified Report é o componente central do Toolkit responsável por agregar os resultados de todos os plugins e gerar relatórios em formato legível. O sistema foi implementado no módulo `toolkit.core.exporters` e trabalha em conjunto com o agregador (`toolkit.core.aggregator`) para transformar dados de análise em relatórios partilháveis.
O utilizador interage com o sistema através do CLI, executando análises e especificando o formato de saída desejado. O processo é completamente automático: os plugins são executados, os resultados agregados, e o relatório final gerado no formato escolhido.


2. Como a Análise e Exportação são Executadas
Para usar o sistema de relatórios, o utilizador precisa apenas de executar o comando de análise através do CLI, especificando opcionalmente o formato de saída desejado.
O processo segue estes passos automaticamente:
    1-Execução de Plugins
    O core executa todos os plugins activados no `toolkit.toml` sobre os ficheiros analisados.

    2-Agregação de Resultados
    A função `aggregate()` recolhe os outputs de cada plugin e consolida-os num relatório unificado.

    3-Geração de Relatório
    Conforme o formato especificado, o sistema gera o relatório final:
        - JSON (padrão): Estrutura de dados completa e processável por máquinas
        - HTML: Visualização formatada e legível para humanos

    Este fluxo é completamente automático: o utilizador não precisa de chamar funções individualmente ou manipular dados manualmente.


3. Como Gerar Relatórios
    1-Relatório JSON (Padrão)
```bash
# Analisar um ficheiro
python -m toolkit.core.cli analyze src/main.py --out report.json

# Analisar múltiplos ficheiros
python -m toolkit.core.cli analyze src/*.py --out report.json

# Analisar diretório completo
python -m toolkit.core.cli analyze src/ --out report.json
```
    2-Relatório HTML (Visual)
```bash
# HTML automático (detectado pela extensão)
python -m toolkit.core.cli analyze src/ --out quality_report.html

# Abrir no browser
xdg-open quality_report.html  # Linux
start quality_report.html      # Windows
open quality_report.html       # macOS
```
    O sistema detecta automaticamente o formato baseado na extensão do ficheiro (`.json` ou `.html`).

    3-Executar Apenas Plugins Específicos
```bash
# Apenas DeadCodeDetector e SecurityChecker
python -m toolkit.core.cli analyze src/ \
  --plugins DeadCodeDetector,SecurityChecker \
  --out report.html

# Apenas StyleChecker
python -m toolkit.core.cli analyze src/ \
  --plugins StyleChecker \
  --out style_report.json
```
    4-Fail-on-Severity (Para CI/CD)
```bash
# Falha se houver issues HIGH
python -m toolkit.core.cli analyze src/ \
  --out report.json \
  --fail-on-severity high

# Verificar exit code
echo $?
# 0 = Sucesso (sem HIGH)
# 3 = Falha (encontrou HIGH)
```


4. Estrutura do Relatório Unificado
O relatório gerado segue uma estrutura consistente, independentemente do formato de saída:
    1-Metadata da Análise
```json
"analysis_metadata": {
  "timestamp": "2025-12-01T10:30:00Z",
  "tool_version": "1.0.0",
  "status": "completed",
  "plugins_executed": ["StyleChecker", "SecurityChecker", "DependencyGraph"]
}
```
    - timestamp: Data e hora ISO 8601
    - tool_version: Versão do toolkit
    - status: `"completed"`, `"partial"` (se plugin falhou), ou `"failed"`
    - plugins_executed: Lista de plugins executados

    2-Sumário Agregado
```json
"summary": {
  "total_files": 12,
  "total_issues": 45,
  "issues_by_severity": {
    "high": 2,
    "medium": 15,
    "low": 28,
    "info": 0
  },
  "issues_by_plugin": {
    "StyleChecker": 30,
    "SecurityChecker": 15
  },
  "top_offenders": [
    {"file": "main.py", "issues": 12},
    {"file": "utils.py", "issues": 8}
  ]
}
```

    3-Detalhes por Ficheiro
```json
"details": [
  {
    "file": "src/main.py",
    "plugins": [
      {
        "plugin": "StyleChecker",
        "summary": {
          "issues_found": 5,
          "status": "completed"
        },
        "results": [
          {
            "severity": "low",
            "code": "STYLE-001",
            "message": "Linha excede 88 caracteres",
            "line": 42,
            "col": 1,
            "hint": "Quebrar linha ou refatorar"
          }
        ]
      }
    ]
  }
]
```


5. Formato HTML Gerado
O HTML gerado pela função `generate_html()` tem esta estrutura:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Code Quality Report</title>
</head>
<body>
    <h1>Code Quality Toolkit Report</h1>
    
    <!-- Metadata -->
    <h2>Analysis Metadata</h2>
    <ul>
        <li><strong>Timestamp:</strong> 2025-12-01T10:30:00Z</li>
        <li><strong>Tool Version:</strong> 1.0.0</li>
        <li><strong>Status:</strong> completed</li>
        <li><strong>Plugins Executed:</strong> StyleChecker, SecurityChecker</li>
    </ul>
    
    <!-- Summary -->
    <h2>Summary</h2>
    <h3>Totals</h3>
    <ul>
        <li><strong>Total Files:</strong> 5</li>
        <li><strong>Total Issues:</strong> 23</li>
    </ul>
    
    <h3>Issues by Severity</h3>
    <ul>
        <li>high: 2</li>
        <li>medium: 8</li>
        <li>low: 13</li>
        <li>info: 0</li>
    </ul>
    
    <h3>Top Offenders</h3>
    <ul>
        <li><strong>main.py</strong>: 10 issues</li>
        <li><strong>utils.py</strong>: 7 issues</li>
    </ul>
    
    <!-- Details por ficheiro -->
    <h2>Details</h2>
    <h3>File: main.py</h3>
    
    <h4>Plugin: StyleChecker</h4>
    <ul>
        <li>Status: completed</li>
        <li>Issues Found: 5</li>
    </ul>
    <ul>
        <li>
            <strong>[LOW]</strong> [STYLE-001] Linha excede 88 caracteres
            (Line 42, Col 1)
            <br><em>Hint: Quebrar linha ou refatorar</em>
        </li>
    </ul>
</body>
</html>
```
    Características do HTML:
        - Standalone (sem CSS/JS externo)
        - UTF-8 encoding
        - XSS-safe (`html.escape()` usado)
        - Mostra todos os plugins (mesmo sem issues)


6. Comportamento com Erros de Plugins
O sistema implementa error handling robusto conforme testado em `test_cli_failure.py`:
    1-Plugin Crash Durante Execução
    Se um plugin lançar uma excepção durante `analyze()`:
```python
class Plugin:
    def analyze(self, source_code: str, file_path: str | None):
        raise RuntimeError("Something went terribly wrong!")
```

    Comportamento:
        - O CLI não crasha (sem traceback Python)
        - Relatório é gerado com `status: "partial"`
        - Erro capturado como issue HIGH:
            {
                "severity": "high",
                "code": "PLUGIN_ERROR",
                "message": "Runtime error: Something went terribly wrong!",
                "line": 0,
                "col": 0
            }
        
        - Exit code: `0` (SUCCESS) se não houver `--fail-on-severity`

    2-Falha ao Carregar Plugin
    Se um plugin não pode ser carregado (dependências em falta):
        - Exit code: `1` (EXIT_MANAGED_ERROR)
        - Mensagem de erro impressa em stderr
        - Relatório não é gerado

    3-Crash do Core System
    Se o core system crashar completamente:
        - Exit code: `2` (EXIT_UNEXPECTED_ERROR)

    4-Fail-on-Severity
    Com flag `--fail-on-severity`:
```bash
python -m toolkit.core.cli analyze src/ --fail-on-severity high
```
        - Se houver issues HIGH (incluindo PLUGIN_ERROR):
        - Exit code: `3` (EXIT_SEVERITY_ERROR)
        - Caso contrário:
        - Exit code: `0` (SUCCESS)


7. Processamento de Relatórios JSON
    1-Com jq (JSON Processor)
```bash
# Ver total de issues
jq '.summary.total_issues' report.json

# Ver apenas issues HIGH
jq '.summary.issues_by_severity.high' report.json

# Listar top 3 piores ficheiros
jq '.summary.top_offenders[:3]' report.json

# Filtrar apenas issues HIGH
jq '.details[].plugins[].results[] | 
    select(.severity=="high")' report.json

# Issues de um plugin específico
jq '.details[].plugins[] | 
    select(.plugin=="SecurityChecker") | 
    .results[]' report.json

# Contar issues por plugin
jq '.summary.issues_by_plugin' report.json

# Ver status da análise
jq '.analysis_metadata.status' report.json
```

    2-Com Python
```python
import json

# Carregar relatório
with open('report.json') as f:
    report = json.load(f)

# Estatísticas básicas
total = report['summary']['total_issues']
high = report['summary']['issues_by_severity']['high']
print(f"Total: {total}, Críticos: {high}")

# Filtrar issues HIGH
high_issues = []
for file_report in report['details']:
    for plugin in file_report['plugins']:
        for issue in plugin['results']:
            if issue['severity'] == 'high':
                high_issues.append({
                    'file': file_report['file'],
                    'plugin': plugin['plugin'],
                    'message': issue['message'],
                    'line': issue['line']
                })

# Mostrar issues HIGH
for issue in high_issues:
    print(f"{issue['file']}:{issue['line']} - {issue['message']}")

# Top offenders
top = report['summary']['top_offenders'][:5]
for rank, offender in enumerate(top, 1):
    print(f"{rank}. {offender['file']}: {offender['issues']} issues")
```


8. Integração com Plugins Reais
Conforme testado em `test_plugins_integration.py`:
    1-DeadCodeDetector
    Código de Teste:
```python
def unused_function():
    pass

def main():
    print('hello')
```

    Comando:
```bash
python -m toolkit.core.cli analyze code.py \
  --plugins DeadCodeDetector \
  --out report.json
```
    Resultado: Reporta issue com mensagem contendo `"unused_function"`

    2-SecurityChecker
    Código de Teste:
```python
def dangerous_code(user_input):
    eval(user_input)  
```

    Comando:
```bash
python -m toolkit.core.cli analyze code.py \
  --plugins SecurityChecker \
  --out report.json
```
    Resultado: Issue com severity `"high"` ou `"medium"`, mensagem sobre `"eval"`

    3-StyleChecker
    Código de Teste:
```python
print('A' * 100) 
```

    Comando:
```bash
python -m toolkit.core.cli analyze code.py \
  --plugins StyleChecker \
  --out report.json
```
    Resultado: Issue sobre `"length"` ou `"characters"`, severity `"low"`


9. Casos de Uso Práticos
    1-Desenvolvimento Local - Revisão Rápida
```bash
# Analisar ficheiro actual
python -m toolkit.core.cli analyze meu_codigo.py --out review.html

# Abrir no browser
firefox review.html
```

    2-CI/CD - Pipeline GitHub Actions
```yaml
name: Code Quality Check

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install Toolkit
        run: |
          pip install -e .
          make setup
      
      - name: Run Analysis
        run: |
          python -m toolkit.core.cli analyze src/ \
            --out report.json \
            --fail-on-severity high
      
      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: quality-report
          path: report.json
```

    3-Script de Análise Periódica
```bash
#!/bin/bash
# daily_quality.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="quality_reports"

mkdir -p "$REPORT_DIR"

echo "A executar análise..."
python -m toolkit.core.cli analyze src/ \
  --out "$REPORT_DIR/report_$DATE.json"

# Gerar HTML
python -m toolkit.core.cli analyze src/ \
  --out "$REPORT_DIR/report_$DATE.html"

# Extrair estatísticas
TOTAL=$(jq '.summary.total_issues' "$REPORT_DIR/report_$DATE.json")
HIGH=$(jq '.summary.issues_by_severity.high' "$REPORT_DIR/report_$DATE.json")

echo "Resultados: $TOTAL issues ($HIGH críticos)"

# Enviar email se houver críticos
if [ "$HIGH" -gt 0 ]; then
  mail -s "Issues críticos!" \
       -a "$REPORT_DIR/report_$DATE.html" \
       team@example.com <<< "Encontrados $HIGH issues críticos."
fi
```

    4-Comparação de Tendências
```python
#!/usr/bin/env python3
"""Comparar dois relatórios"""
import json
import sys

def compare_reports(old_path, new_path):
    with open(old_path) as f:
        old = json.load(f)
    with open(new_path) as f:
        new = json.load(f)
    
    old_total = old['summary']['total_issues']
    new_total = new['summary']['total_issues']
    diff = new_total - old_total
    
    print(f"   Comparação de Relatórios")
    print(f"   Anterior: {old_total} issues")
    print(f"   Actual: {new_total} issues")
    print(f"   Diferença: {diff:+d} issues")
    
    if diff > 0:
        print("   Qualidade piorou!")
        return 1
    elif diff < 0:
        print("   Qualidade melhorou!")
        return 0
    else:
        print("   Sem alterações")
        return 0

if __name__ == '__main__':
    sys.exit(compare_reports(sys.argv[1], sys.argv[2]))
```

**Uso**:
```bash
python compare_reports.py report_20251130.json report_20251201.json
```


10. Troubleshooting Detalhado
    1-HTML não é válido
    Sintoma: Browser não abre ou mostra erro

    Verificar:
```bash
# Confirmar que é HTML válido
file report.html
# Deve mostrar: "HTML document, UTF-8 Unicode text"

# Ver primeiras linhas
head -5 report.html
# Deve começar com: <!DOCTYPE html>

# Verificar tamanho
ls -lh report.html
# Se for 0 bytes, não foi gerado
```

    Solução:
        - Verificar se comando CLI executou sem erros
        - Ver stderr: `python -m toolkit.core.cli ... 2>&1 | tee log.txt`

    2-Relatório mostra "partial"
    Sintoma: Status no HTML diz `"partial"` 
    Causa: Um ou mais plugins crasharam durante execução
    Diagnóstico:
```bash
# Ver qual plugin falhou
jq '.details[].plugins[] | 
    select(.summary.status=="failed") | 
    .plugin' report.json

# Ver o erro específico
jq '.details[].plugins[] | 
    select(.summary.status=="failed") | 
    .summary.error' report.json

# Ver issues PLUGIN_ERROR
jq '.details[].plugins[].results[] | 
    select(.code=="PLUGIN_ERROR")' report.json
```
    Solução:
        - Verificar dependências do plugin
        - Ver log de erro no relatório
        - Executar plugin isoladamente para debug

    3-Exit code inesperado (3)
    Sintoma: Pipeline CI falha com exit code 3
    Causa: Há issues HIGH no código (ou plugin crashou)
    Diagnóstico:
```bash
# Contar issues HIGH
jq '[.details[].plugins[].results[] | 
     select(.severity=="high")] | length' report.json

# Listar todos os HIGH
jq '.details[].plugins[].results[] | 
    select(.severity=="high") | 
    {file: .file, plugin: .plugin, message: .message, line: .line}' report.json

# Ver se é PLUGIN_ERROR
jq '[.details[].plugins[].results[] | 
     select(.code=="PLUGIN_ERROR")] | length' report.json
```
    Solução:
        - Se for PLUGIN_ERROR: corrigir plugin ou dependências
        - Se for issue real: corrigir código
        - Se quiser ignorar temporariamente: remover `--fail-on-severity`

    4-Contagens incorrectas
    Sintoma: Total não bate certo
    Verificação Manual:
```bash
# Contar manualmente
jq '[.details[].plugins[].results[]] | length' report.json

# Comparar com total reportado
jq '.summary.total_issues' report.json
```

    Solução:
        - Executar testes: `pytest tests/core/test_exporters.py -v`
        - Se testes passam, pode ser bug: reportar issue

    5-HTML não mostra todos os plugins
    Sintoma: Falta um plugin no HTML
    Verificar:
```bash
# Ver plugins executados
jq '.analysis_metadata.plugins_executed' report.json

# Ver plugins em details
jq '[.details[].plugins[].plugin] | unique' report.json
```

    Causa Provável: Plugin não está em `toolkit.toml` ou não foi solicitado em `--plugins`
    Solução:
```bash
# Ver config
cat toolkit.toml | grep -A 5 '\[plugins\]'

# Executar com plugin específico
python -m toolkit.core.cli analyze src/ \
  --plugins DeadCodeDetector,StyleChecker \
  --out report.html
```


11. Pré-requisitos e Considerações
    1-Sem Dependências Externas
    O sistema de relatórios não requer bibliotecas externas além do Python padrão:
        - Agregação usa estruturas nativas (`dict`, `list`)
        - Geração de HTML usa string templates simples
        - Parsing de JSON usa biblioteca padrão `json`
        - Excepção: Módulo `html` (stdlib) para `html.escape()`

    2-Robustez
    O sistema está preparado para:
        - Plugins com falhas (status `"partial"`)
        - Dados vazios (funciona com 0 issues)
        - Ficheiros grandes (processamento eficiente)
        - XSS attacks (escape automático)

    3-Validação de Schema
    O sistema valida automaticamente que:
        - Todos os plugins devolvem schema esperado
        - Relatório final contém todas as chaves obrigatórias
        - Dados agregados mantêm consistência matemática

    Verificado por testes:
    - `test_aggregate_counts_total_issues_correctly()`
    - `test_aggregate_counts_by_severity_correctly()`
    - `test_aggregate_counts_by_plugin_correctly()`