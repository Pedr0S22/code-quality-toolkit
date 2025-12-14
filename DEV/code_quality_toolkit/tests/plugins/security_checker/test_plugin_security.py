import os
from pathlib import Path
from textwrap import dedent

import pytest

# --- IMPORTS ---
import src.toolkit.plugins.security_checker.plugin as plugin_module
from src.toolkit.plugins.security_checker.plugin import Plugin
from src.toolkit.utils.config import ToolkitConfig


# ==============================================================================
# PEÇA QUE FALTAVA: O Setup do Caminho Real (Sem isso os testes de baixo falham)
# ==============================================================================
@pytest.fixture
def real_dashboard_path():
    """Define onde o ficheiro HTML vai ser criado e limpa o lixo."""
    # Descobre a pasta onde está o plugin.py
    plugin_dir = Path(plugin_module.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    # Apaga se já existir (começar limpo)
    if target_file.exists():
        os.remove(target_file)
    
    yield target_file  # Entrega o caminho para o teste usar

    # Apaga depois do teste acabar (limpar a casa)
    if target_file.exists():
        os.remove(target_file)

# ==============================================================================
# OS TEUS TESTES DE DETEÇÃO (Mantidos exatamente como querias)
# ==============================================================================

def test_security_checker_detects_eval() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent("""
        def process(user_code):
            result = eval(user_code)
            return result
    """)

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1
    assert any(i["code"] == "B307" for i in report["results"])

def test_security_checker_detects_exec() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "exec(user_input)"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_sql_injection() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "cursor.execute('SELECT * FROM %s' % table)"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_shell_injection() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "import os\nos.system('cp ' + x)"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_pickle() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "import pickle\npickle.load(f)"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_hardcoded_password() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = 'PASSWORD = "123"'
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_weak_hash() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "import hashlib\nhashlib.md5(b'data')"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_report_structure() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("eval('t')", "test.py")
    assert "results" in report
    assert "summary" in report

def test_security_checker_metadata() -> None:
    plugin = Plugin()
    metadata = plugin.get_metadata()
    assert metadata["name"] == "SecurityChecker"

def test_multiple_vulnerabilities() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "eval('a')\nimport pickle\npickle.load(f)\nPASSWORD='123'"
    report = plugin.analyze(code, "test.py")
    assert report["summary"]["issues_found"] >= 3

def test_empty_file() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("", "empty.py")
    assert report["summary"]["issues_found"] == 0

def test_syntax_error_handling() -> None:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("def broken(\n  eval(", "broken.py")
    assert report["summary"]["status"] in ["completed", "failed"]

# ==============================================================================
# OS TESTES DO DASHBOARD (Reais, no disco, simples)
# ==============================================================================

def test_generate_dashboard_creates_real_file_on_disk(real_dashboard_path):
    """Cria ficheiro real, verifica se existe, e valida conteúdo."""
    plugin = Plugin()
    
    # Dados simulados
    real_data = [
        {"severity": "high", "code": "B307", "file": "login.py"},
        {"severity": "medium", "code": "B105", "file": "config.py"},
        {"severity": "low", "code": "B101", "file": "utils.py"}
    ]

    # Ação (Escreve no disco)
    plugin.generate_dashboard(real_data)

    # Validação Física
    assert real_dashboard_path.exists()
    assert real_dashboard_path.stat().st_size > 0

    # Validação de Conteúdo
    content = real_dashboard_path.read_text(encoding="utf-8")
    assert '"total_issues": 3' in content
    assert '"file": "login.py"' in content
    assert "SecurityChecker Analysis" in content

def test_generate_dashboard_with_empty_list_real(real_dashboard_path):
    """Testa dashboard vazio."""
    plugin = Plugin()
    plugin.generate_dashboard([])

    assert real_dashboard_path.exists()
    content = real_dashboard_path.read_text(encoding="utf-8")
    assert '"total_issues": 0' in content

def test_generate_dashboard_handles_missing_keys_real(real_dashboard_path):
    """Testa resiliência com dados incompletos."""
    plugin = Plugin()
    broken_data = [{"severity": "high"}] # Falta code e file

    plugin.generate_dashboard(broken_data)

    assert real_dashboard_path.exists()
    content = real_dashboard_path.read_text(encoding="utf-8")
    assert 'unknown' in content # Usa default para nome do ficheiro