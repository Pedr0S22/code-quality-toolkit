Membros:

João Neto  2023234004  @Imajellyfish  
João Eduardo Duarte  2011187848  @jeduarteldm  
Bernardo Fonseca  2021239253  @jF202  
Diogo Delvivo  2021150174  @delvivo.diogo1  
Catarina Vieira 2023218473  @27634982


Análise do código do Core Unified Report

1. Propósito e Utilidade Geral
Este código implementa o sistema central de agregação e exportação de relatórios do Code Quality Toolkit. Composto por 2 módulos principais (`aggregator.py` e `exporters.py`), o sistema é responsável por recolher os outputs individuais de todos os plugins executados, consolidá-los numa estrutura unificada e transformá-los em formatos consumíveis tanto por humanos (HTML) como por máquinas (JSON).
A utilidade prática é fundamental: permite que diferentes plugins trabalhem independentemente, produzindo outputs no mesmo formato, que são depois combinados automaticamente num relatório coerente. Este tipo de sistema é essencial em ferramentas de análise estática modulares, pipelines de qualidade de código, relatórios de conformidade e processos de revisão automatizada.


2. Funcionamento do Sistema
O sistema está organizado em duas fases principais: agregação e exportação.
    1-Fase 1: Agregação de Resultados
    A função `aggregate()` no módulo `aggregator.py` é o coração do sistema. Recebe uma lista de resultados por ficheiro (cada um contendo outputs de múltiplos plugins) e um dicionário com o estado de execução de cada plugin.

    O processo de agregação segue esta lógica:

    1) Inicialização de Estruturas
    Cria contadores para severidades (`high`, `medium`, `low`, `info`) e para issues por plugin, inicializados todos a zero.

    2) Iteração por Ficheiros
    Para cada ficheiro analisado:
        - Itera sobre os resultados de cada plugin executado nesse ficheiro
        - Extrai a lista de issues do campo `results`
        - Para cada issue encontrado:
        - Incrementa o contador da severidade correspondente
        - Incrementa o contador do plugin que encontrou o issue
        - Acumula no total geral

    3) Cálculo de Top Offenders
    Constrói uma lista de tuplas (ficheiro, contagem) agregando todos os issues por ficheiro, ordena por contagem descendente, e converte para formato de dicionário.

    4) Construção de Metadata
    Recolhe informação sobre a análise:
        - Timestamp da execução
        - Versão do toolkit
        - Lista de plugins executados
        - Estado geral (`completed` se todos os plugins succeeded, `partial` se algum falhou)

    5) Montagem do Relatório Final
    Combina metadata, sumário agregado e detalhes completos numa estrutura `UnifiedReport` que segue o schema definido no documento de especificação.

    A agregação é matematicamente rigorosa: todos os contadores são validados por testes unitários que garantem que a soma total é consistente e que não há duplicações ou perdas de informação.

    2-Fase 2: Exportação para HTML
    A função `generate_html()` no módulo `exporters.py` transforma o relatório unificado em HTML legível. O processo é essencialmente um template engine simples:
    1) Estrutura Base
    Cria o esqueleto HTML com DOCTYPE, head com charset UTF-8, e body estruturado:
        output = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Code Quality Report</title>
        </head>
        <body>
            <h1>Code Quality Toolkit Report</h1>
        """
    

    2) Secção de Metadata  
    Renderiza informações de alto nível:
        metadata = report["analysis_metadata"]
        output += f"<li><strong>Timestamp:</strong> {metadata['timestamp']}</li>"
        output += f"<li><strong>Tool Version:</strong> {metadata['tool_version']}</li>"
        output += f"<li><strong>Status:</strong> {metadata['status']}</li>"
        plugins_list = ", ".join(metadata["plugins_executed"])
        output += f"<li><strong>Plugins Executed:</strong> {plugins_list}</li>"
    

    3) Secção de Sumário
    Gera 3 sub-secções:
        - Totais: Total de ficheiros e total de issues
        - Issues by Severity: Lista não-ordenada com cada severidade e sua contagem
        - Issues by Plugin: Lista não-ordenada com cada plugin e quantos issues encontrou
        - Top Offenders: Lista ordenada dos ficheiros mais problemáticos

    4) Secção de Detalhes
    Para cada ficheiro analisado:
        for file_report in details:
            output += f"<h3>File: {file_report['file']}</h3>"
            
            for plugin_run in file_report['plugins']:
                plugin_name = plugin_run['plugin']
                p_summary = plugin_run['summary']
                results = plugin_run['results']
                
                output += f"<h4>Plugin: {plugin_name}</h4>"
                output += f"<li>Status: {p_summary['status']}</li>"
                output += f"<li>Issues Found: {p_summary['issues_found']}</li>"

    Para cada plugin:
        - Cabeçalho com nome do plugin
        - Informação de estado e métricas
        - Se houver erros, exibe-os
        - Se houver issues, renderiza lista HTML com cada issue contendo:
        - Severidade em uppercase
        - Código do issue
        - Mensagem (escaped com `html.escape()` para segurança)
        - Linha e coluna
        - Hint explicativa (também escaped)

    Importante: O HTML exibe todos os plugins, mesmo os que não encontraram issues, mostrando 'No issues found' nesse caso.

    5) Escape de HTML (Segurança XSS)
    msg = html.escape(issue.get('message', ''))
    hint = html.escape(issue.get('hint', ''))

    Usa `html.escape()` em todas as mensagens user-provided para prevenir ataques Cross-Site Scripting (XSS).
    O HTML gerado é standalone, ou seja, não depende de CSS externo ou JavaScript, podendo ser aberto em qualquer browser moderno sem configuração adicional.


3. Qualidade da Implementação
O código demonstra várias boas práticas de engenharia de software:
    1-Separação de Responsabilidades
    A clara divisão entre agregação (`aggregator.py`) e exportação (`exporters.py`) facilita manutenção e testes. Cada módulo tem uma responsabilidade única bem definida.

    2-Robustez e Error Handling
    O sistema está preparado para:
        - Plugins que falham: Mantém o erro no campo `error` do sumário e status `"partial"`
        - Dados vazios: Funciona corretamente com 0 issues
        - Campos opcionais ausentes: Usa `.get()` com fallbacks (`''`, `'?'`)

    3-Validação Matemática
    Os testes unitários em `test_exporters.py` validam rigorosamente:
        - Precisão de Contagens: Verifica que `total_issues == sum(all issues)`
        - Agrupamento Correcto: Confirma que `issues_by_severity` soma correctamente
        - Ordenação: Garante que `top_offenders` está ordenado descendentemente
        - Schema Integrity: Valida que todas as chaves obrigatórias existem

    4-Segurança - Prevenção de XSS
    O uso de `html.escape()` previne vulnerabilidades XSS, essencial quando se renderiza conteúdo user-provided:
        msg = html.escape(issue.get('message', ''))
        hint = html.escape(issue.get('hint', ''))

    Isto converte caracteres perigosos:
        - `<script>` → `&lt;script&gt;`
        - `"` → `&quot;`
        - `&` → `&amp;`

    Previne que código malicioso seja executado quando o HTML é aberto.

    5-Type Hints
    O uso de type hints (`dict[str, Any]`, `list`, etc.) melhora a legibilidade e permite detecção estática de erros com ferramentas como `mypy`.

    6-Testabilidade
    O design modular permite testes unitários isolados. A função `create_mock_result()` nos testes demonstra como é fácil criar dados de teste que passam validação:
        def create_mock_result(severity="low", code="TEST001", count=1):
            results = []
            for _ in range(count):
                results.append({
                    "severity": severity,
                    "code": code,
                    "message": "Mock error message",
                    "line": 1,
                    "col": 1
                })
            return {
                "results": results,
                "summary": {
                    "issues_found": count,
                    "status": "completed"
                }
            }


4. Arquitectura de Testes
O sistema implementa três níveis de testes:
    1-Testes de Precisão Matemática (`test_exporters.py`)
    test_aggregate_counts_total_issues_correctly()
    Valida soma total de issues:
```python
mock_files = [
    {"file": "file_A.py", "plugins": [...]}  # 2 issues
    {"file": "file_B.py", "plugins": [...]}  # 1 issue
]
report = aggregate(mock_files, mock_status)
assert report["summary"]["total_issues"] == 3  # 2 + 1
```

    test_aggregate_counts_by_severity_correctly()
    Valida distribuição por severidade:
```python
# Input: 1 high, 2 medium, 1 low
assert summary["issues_by_severity"]["high"] == 1
assert summary["issues_by_severity"]["medium"] == 2
assert summary["issues_by_severity"]["low"] == 1
assert summary["issues_by_severity"]["info"] == 0
```

    test_aggregate_counts_by_plugin_correctly() 
    Valida contagem por plugin:
```python
# PluginA aparece em 2 ficheiros: 1 + 1 = 2
assert summary["issues_by_plugin"]["PluginA"] == 2
# PluginB aparece em 1 ficheiro: 3
assert summary["issues_by_plugin"]["PluginB"] == 3
```

    2-Testes de Lógica de Ordenação
    test_top_offenders_sorting_logic()
    Garante que worst offenders aparecem primeiro:
```python
mock_files = [
    {"file": "worst_offender.py", ...},  # 50 issues
    {"file": "bad_offender.py", ...},    # 5 issues
    {"file": "clean.py", ...}            # 0 issues
]

top = report["summary"]["top_offenders"]
assert top[0]["file"] == "worst_offender.py"
assert top[0]["issues"] == 50
assert top[1]["file"] == "bad_offender.py"
assert top[1]["issues"] == 5
```

    3-Testes de Robustez (`test_cli_failure.py`)
    Plugin Crash Durante Execução 
```python
class Plugin:
    def analyze(self, source_code: str, file_path: str | None):
        raise RuntimeError("Something went terribly wrong!")

def test_cli_partial_report_on_plugin_runtime_failure():
    # 1. CLI não crasha (sem traceback Python)
    exit_code = main([...])
    assert exit_code == EXIT_SUCCESS
    
    # 2. Relatório gerado com status "partial"
    assert data["analysis_metadata"]["status"] == "partial"
    
    # 3. Erro capturado como issue HIGH
    assert error_entry["code"] == "PLUGIN_ERROR"
    assert "Something went terribly wrong" in error_entry["message"]
```

    Core System Crash  
```python
def test_cli_crash_safety_net():
    with patch("toolkit.core.cli.run_analysis", 
               side_effect=Exception("Core Meltdown")):
        exit_code = main([...])
    
    assert exit_code == 2  # EXIT_UNEXPECTED_ERROR
```

    Fail on Severity
```python
def test_cli_exit_code_on_severity_failure():
    # Plugin crashou → gera issue HIGH
    exit_code = main([..., "--fail-on-severity", "high"])
    assert exit_code == EXIT_SEVERITY_ERROR  # 3
```

    4-Testes de Integração (`test_plugins_integration.py`)
    Dead Code Detector  
```python
code_file.write_text(
    "def unused_function():\n"
    "    pass\n"
)

exit_code = main(["analyze", ..., "--plugins", "DeadCodeDetector"])
assert "unused_function" in issue["message"]
```

    Security Checker 
```python
code_file.write_text(
    "def dangerous_code(user_input):\n"
    "    eval(user_input)\n"
)

exit_code = main(["analyze", ..., "--plugins", "SecurityChecker"])
assert "eval" in issue["message"].lower()
assert issue["severity"] in ["medium", "high"]
```

    Style Checker 
```python
long_line = "print('" + "A" * 100 + "')"
code_file.write_text(f"{long_line}\n")

exit_code = main(["analyze", ..., "--plugins", "StyleChecker"])
assert "length" in issue["message"].lower()
```


5. Arquitectura de Exit Codes
O sistema implementa exit codes semânticos para facilitar integração com CI/CD:
    Uso em CI/CD:
```bash
python -m toolkit.core.cli analyze src/ --fail-on-severity high

if [ $? -eq 3 ]; then
  echo "Issues críticos encontrados!"
  exit 1
elif [ $? -eq 2 ]; then
  echo "Sistema crashou!"
  exit 1
elif [ $? -eq 1 ]; then
  echo "Erro ao carregar plugins"
  exit 1
else
  echo "Análise OK"
fi
```


6. Integração com o Core System
O Unified Report integra-se perfeitamente com o resto do toolkit:
    1-Contrato de Plugin Respeitado
    Todos os plugins devolvem estrutura compatível:
        {
            "results": [...],
            "summary": {
                "issues_found": int,
                "status": str
            }
        }

    2-CLI Integration
    O CLI (`cli.py`) orquestra:
        1. Descoberta e carregamento de plugins
        2. Execução de plugins em cada ficheiro
        3. Agregação via `aggregate()`
        4. Exportação via `generate_html()` ou JSON nativo

    3-Extensibilidade
    Adicionar novo exportador é trivial:
```python
# Em exporters.py
def generate_markdown(report: UnifiedReport) -> str:
    # Implementation
    pass

# No CLI
if output_path.endswith('.md'):
    content = generate_markdown(report)
```


7. Utilidade Prática
Em ambiente real, este sistema é fundamental para:
    1-Comunicação de Resultados
    Transforma dados técnicos em formatos compreensíveis:
        - Developers: HTML visual para revisão rápida
        - CI Systems: JSON para decisões automatizadas
        - Management: Relatórios formatados para tracking de qualidade

    2-Rastreabilidade e Auditoria
    Relatórios timestamped permitem:
        - Acompanhar evolução de métricas ao longo do tempo
        - Provar conformidade com standards
        - Identificar regressões em qualidade

    3-Facilitação de Workflows
    Integra-se naturalmente em:
        - Pre-commit hooks: Validação local antes de commit
        - Pull request checks: Comentários automáticos com findings
        - Scheduled scans: Relatórios periódicos por email

    4-Tomada de Decisões
    O sumário agregado facilita:
        - Priorização de refactoring (focar em top offenders)
        - Alocação de recursos (plugins com mais issues)
        - Tracking de KPIs (tendência de issues ao longo do tempo)