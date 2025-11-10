"""Testes Unitários para o StyleCheckerPlugin (Tarefa #99)."""

# Importar o plugin (nome da classe 'Plugin')
from toolkit.plugins.style_checker.plugin import Plugin
# REMOVA: from toolkit.utils.config import ToolkitConfig

# --- Mocks para resolver o erro 'AttributeError: 'RulesConfig' object attribute 'indent_style' is read-only' ---
class MockRulesConfig:
    """Mock 'read-only' para permitir a configuração das regras no teste."""
    max_line_length = 88
    check_whitespace = True
    indent_style = "spaces" 
    indent_size = 4
    allow_mixed_indentation = False

class MockToolkitConfig:
    """Mock do ToolkitConfig que usa o MockRulesConfig."""
    def __init__(self):
        self.rules = MockRulesConfig()
# --------------------------------------------------------------------

def test_style_checker_flags_long_line():
    """Verifica a regra LINE_LENGTH e a conformidade com o Contrato NOVO."""
    
    plugin = Plugin()
    config = MockToolkitConfig() # MUDANÇA: Usar o Mock
    config.rules.max_line_length = 10
    plugin.configure(config)

    report = plugin.analyze("linha muito longa", "sample.py")

    # A. Verificar Sumário e Contrato
    assert report["summary"]["issues_found"] == 1
    assert "plugin" in report # <--- CORREÇÃO (Contrato Novo)
    assert report["plugin"]["name"] == "StyleChecker"
    
    # B. Verificar Ocorrência
    issue = report["results"][0]
    assert issue["metric"] == "LINE_LENGTH" # <--- CORREÇÃO (era 'code')
    assert issue["value"] == 17             # <--- CORREÇÃO (novo campo)
    assert issue["entity"] == "Linha 1"     # <--- CORREÇÃO (novo campo)
    assert issue["severity"] == "low"

def test_style_checker_flags_trailing_whitespace():
    """Verifica a nova regra TRAILING_WHITESPACE (Contrato NOVO)."""
    
    plugin = Plugin()
    config = MockToolkitConfig() # MUDANÇA: Usar o Mock
    config.rules.check_whitespace = True
    plugin.configure(config)
    
    source_code = "linha com espaco no fim \nlinha limpa"
    report = plugin.analyze(source_code, "whitespace.py")
    
    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]
    assert issue["metric"] == "TRAILING_WHITESPACE" # <--- CORREÇÃO (era 'code')
    assert issue["line"] == 1

def test_style_checker_flags_indentation_tabs():
    """Verifica a nova regra INDENT_TABS_NOT_ALLOWED (Contrato NOVO)."""
    
    plugin = Plugin()
    config = MockToolkitConfig() # MUDANÇA: Usar o Mock
    config.rules.indent_style = "spaces" 
    plugin.configure(config)
    
    source_code = "\tprint('hello')"
    report = plugin.analyze(source_code, "indent.py")
    
    assert report["summary"]["issues_found"] >= 1
    
    # <--- CORREÇÃO (procurar por 'metric')
    indent_issue = next((r for r in report["results"] if r["metric"] == "INDENT_TABS_NOT_ALLOWED"), None)
    assert indent_issue is not None
    assert indent_issue["line"] == 1

def test_style_checker_no_issues_found():
    """Verifica código limpo (Contrato NOVO)."""
    
    plugin = Plugin()
    config = MockToolkitConfig() # MUDANÇA: Usar o Mock
    plugin.configure(config)

    source_code = "def fn():\n    pass\n"
    report = plugin.analyze(source_code, "good_file.py")

    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0