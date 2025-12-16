"""Testes Unitários para o StyleCheckerPlugin (Tarefa #98)."""

# Importar o plugin (nome da classe 'Plugin')
from toolkit.plugins.style_checker.plugin import Plugin

# REMOVA: from toolkit.utils.config import ToolkitConfig


# --- Mocks para resolver o erro 'AttributeError:
# 'RulesConfig' object attribute 'indent_style' is read-only'
# ---
class MockRulesConfig:
    """Mock 'read-only' para permitir a configuração das regras no teste."""

    max_line_length = 88
    check_whitespace = True
    indent_style = "spaces"
    indent_size = 4
    allow_mixed_indentation = False
    check_naming = True  # <-- 1. ADICIONAR ESTA LINHA


class MockToolkitConfig:
    """Mock do ToolkitConfig que usa o MockRulesConfig."""

    def __init__(self):
        self.rules = MockRulesConfig()


# --------------------------------------------------------------------

#
# --- TESTES DE REGRESSÃO (CONTRATO ANTIGO) ---
#


def test_style_checker_flags_long_line():
    """Verifica a regra LINE_LENGTH (Contrato ANTIGO)."""

    plugin = Plugin()
    config = MockToolkitConfig()  # MUDANÇA: Usar o Mock
    config.rules.max_line_length = 10
    plugin.configure(config)

    report = plugin.analyze("linha muito longa", "sample.py")

    assert report["summary"]["issues_found"] == 1

    # VALIDAR O CONTRATO ANTIGO
    issue = report["results"][0]
    assert issue["code"] == "LINE_LENGTH"
    assert "Máximo configurado: 10" in issue["hint"]
    assert issue["line"] == 1


def test_style_checker_flags_trailing_whitespace():
    """Verifica a nova regra TRAILING_WHITESPACE (Contrato ANTIGO)."""

    plugin = Plugin()
    config = MockToolkitConfig()  # Usar o Mock
    config.rules.check_whitespace = True
    plugin.configure(config)

    source_code = "linha com espaco no fim \nlinha limpa"
    report = plugin.analyze(source_code, "whitespace.py")

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]
    assert issue["code"] == "TRAILING_WHITESPACE"
    assert issue["line"] == 1


def test_style_checker_flags_indentation_tabs():
    """Verifica a nova regra INDENT_TABS_NOT_ALLOWED (Contrato ANTIGO)."""

    plugin = Plugin()
    config = MockToolkitConfig()  # MUDANÇA: Usar o Mock
    config.rules.indent_style = "spaces"  # O Mock permite esta atribuição
    plugin.configure(config)

    source_code = "\tprint('hello')"  # Recuo com Tab
    report = plugin.analyze(source_code, "indent.py")

    assert report["summary"]["issues_found"] >= 1

    # Validar que a regra de indentação correta foi ativada
    indent_issue = next(
        (r for r in report["results"] if r["code"] == "INDENT_TABS_NOT_ALLOWED"), None
    )
    assert indent_issue is not None
    assert indent_issue["line"] == 1


def test_style_checker_no_issues_found():
    """Verifica código limpo (Contrato ANTIGO)."""

    plugin = Plugin()
    config = MockToolkitConfig()  # Usar o Mock
    plugin.configure(config)  # Usar defaults

    # Código limpo (agora também verifica naming)
    source_code = "class MyClass:\n    def my_function(self):\n        pass\n"
    report = plugin.analyze(source_code, "good_file.py")

    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0


#
# --- 2. ADICIONAR NOVOS TESTES (TAREFA #98) ---
#


def test_style_checker_flags_class_naming_violation():
    """Verifica a nova regra CLASS_NAMING (Tarefa #98)."""

    plugin = Plugin()
    config = MockToolkitConfig()
    config.rules.check_naming = True  # Ativar a regra
    plugin.configure(config)

    # Classe em snake_case (inválido)
    source_code = "class my_bad_class:\n    pass\n"
    report = plugin.analyze(source_code, "naming.py")

    assert report["summary"]["issues_found"] >= 1

    # Validar que a regra correta foi ativada
    issue = next((r for r in report["results"] if r["code"] == "CLASS_NAMING"), None)
    assert issue is not None
    assert issue["message"] == "Class name 'my_bad_class' deve usar o CamelCase."
    assert issue["line"] == 1


def test_style_checker_flags_function_naming_violation():
    """Verifica a nova regra FUNC_NAMING (Tarefa #98)."""

    plugin = Plugin()
    config = MockToolkitConfig()
    config.rules.check_naming = True  # Ativar a regra
    plugin.configure(config)

    # Função em CamelCase (inválido)
    source_code = "def MyBadFunction():\n    pass\n"
    report = plugin.analyze(source_code, "naming.py")

    assert report["summary"]["issues_found"] >= 1

    # Validar que a regra correta foi ativada
    issue = next((r for r in report["results"] if r["code"] == "FUNC_NAMING"), None)
    assert issue is not None
    assert issue["message"] == "Function name 'MyBadFunction' deve usar o snake_case."
    assert issue["line"] == 1


def test_style_checker_ignores_naming_if_disabled():
    """Verifica se as regras de nomeação são ignoradas se check_naming=False."""

    plugin = Plugin()
    config = MockToolkitConfig()
    config.rules.check_naming = False  # Desativar a regra
    plugin.configure(config)

    # Código com violações
    source_code = "class my_bad_class:\n    def MyBadFunction():\n        pass\n"
    report = plugin.analyze(source_code, "naming.py")

    # Garantir que nenhuma issue de nomeação foi reportada
    class_issue = next(
        (r for r in report["results"] if r["code"] == "CLASS_NAMING"), None
    )
    func_issue = next(
        (r for r in report["results"] if r["code"] == "FUNC_NAMING"), None
    )

    assert class_issue is None
    assert func_issue is None


def test_style_checker_handles_empty_file():
    """Verifica comportamento com ficheiro vazio."""
    plugin = Plugin()
    config = MockToolkitConfig()
    plugin.configure(config)

    report = plugin.analyze("", "empty.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
