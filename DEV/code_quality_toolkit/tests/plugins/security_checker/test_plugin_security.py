import os
import pytest
import json
from pathlib import Path
from textwrap import dedent

# --- IMPORTAÇÃO ESTRITA (Para o Coverage funcionar) ---
# Tem de ser o caminho completo 'src.toolkit...'
from src.toolkit.plugins.security_checker.plugin import Plugin
from src.toolkit.utils.config import ToolkitConfig, PluginsConfig, SecurityCheckerConfig

def test_security_checker_detects_eval() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        def process(user_code):
            result = eval(user_code)
            return result
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1
    assert any(i["code"] == "B307" for i in report["results"])


def test_security_checker_detects_exec() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = "exec(user_input)"
    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_detects_sql_injection() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        def get_user(username):
            query = "SELECT * FROM users WHERE username = '%s'" % username
            cursor.execute(query)
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_detects_shell_injection() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        import os
        def backup(filename):
            os.system("cp " + filename + " /backup/")
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_detects_pickle() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        import pickle
        def load_data(f):
            return pickle.load(f)
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_detects_hardcoded_password() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = 'PASSWORD = "super_secret_123"'
    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_detects_weak_hash() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        import hashlib
        def hash_pwd(pwd):
            return hashlib.md5(pwd.encode()).hexdigest()
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_security_checker_report_structure() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = "eval('test')"
    report = plugin.analyze(code, "test.py")

    assert "results" in report
    assert "summary" in report
    assert "issues_found" in report["summary"]
    assert "status" in report["summary"]

    if report["summary"]["issues_found"] > 0:
        issue = report["results"][0]
        assert "severity" in issue
        assert "code" in issue
        assert "message" in issue
        assert issue["severity"] in ["low", "medium", "high"]


def test_security_checker_metadata() -> None:
    plugin = Plugin()
    metadata = plugin.get_metadata()

    assert metadata["name"] == "SecurityChecker"
    assert "version" in metadata
    assert "description" in metadata


def test_multiple_vulnerabilities() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = dedent(
        """
        import os
        import pickle
        
        PASSWORD = "secret"
        
        def process(user_input, file):
            eval(user_input)
            os.system("cat " + file)
            pickle.load(open(file, 'rb'))
    """
    )

    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 3


def test_empty_file() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    report = plugin.analyze("", "empty.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0


def test_syntax_error_handling() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    code = "def broken(\n    eval("
    report = plugin.analyze(code, "broken.py")

    assert report["summary"]["status"] in ["completed", "failed"]


@pytest.fixture
def dashboard_file():
    """
    Descobre onde o HTML é salvo, apaga antes e apaga depois.
    Usa o próprio objeto Plugin para localizar a pasta, garantindo alinhamento.
    """
    # Truque para pegar o caminho do ficheiro plugin.py sem importar o módulo solto
    import sys
    plugin_module = sys.modules[Plugin.__module__]
    plugin_dir = Path(plugin_module.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    # Limpar antes
    if target_file.exists():
        os.remove(target_file)
    
    yield target_file

    # Limpar depois
    if target_file.exists():
        os.remove(target_file)


# ==========================================
# 2. TESTES DE ANÁLISE REAL (O Core)
# ==========================================

def test_full_lifecycle_with_bandit_real():
    """
    Teste 'E2E' (Ponta a Ponta) do Plugin.
    Executa o caminho feliz inteiro para maximizar o coverage.
    """
    # 1. Inicialização
    plugin = Plugin()
    
    # 2. Configuração (Real)
    sec_conf = SecurityCheckerConfig(report_severity_level="LOW") # Low para apanhar tudo
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    config = ToolkitConfig(plugins=plugins_conf)
    plugin.configure(config)

    # 3. Análise (Real - Cria ficheiro temp, roda Bandit, apaga temp)
    # Código com Eval (High), Password (Low) e Hash (Low)
    code = dedent("""
        import hashlib
        eval('exploit')
        PASSWORD = '123'
        hashlib.md5(b'bad')
    """)
    
    report = plugin.analyze(code, "full_test.py")

    # Validações da Análise
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 3
    
    # Verifica se os códigos do Bandit estão lá
    codes = [r["code"] for r in report["results"]]
    assert "B307" in codes # eval
    assert "B105" in codes # password
    
    # Verifica injeção do nome do ficheiro
    assert report["results"][0]["file"] == "full_test.py"


def test_analyze_sql_injection_real():
    """Teste isolado para SQL Injection (Bandit Real)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    # Bandit deteta isto como B601 (Param) ou B608 (Hardcoded SQL)
    code = "cursor.execute('SELECT * FROM users WHERE name = ' + user_input)"
    report = plugin.analyze(code, "db.py")
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1


def test_analyze_clean_file_real():
    """Teste de ficheiro limpo (Cobre o caminho 'else' e loops vazios)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    report = plugin.analyze("print('Ola Mundo')", "clean.py")
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0


# ==========================================
# 3. TESTES DE CONFIGURAÇÃO (Variantes)
# ==========================================

def test_config_defaults_real():
    """Cobre o caso em que nenhuma config é passada."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    assert plugin.report_severity_level == "LOW"

def test_config_fallback_real():
    """Cobre o bloco 'elif hasattr(...)'."""
    plugin = Plugin()
    config = ToolkitConfig()
    config.plugins.security_checker = None
    
    # Simulando objeto genérico para config antiga
    class OldRules:
        security_report_level = "MEDIUM"
    config.rules = OldRules()

    plugin.configure(config)
    assert plugin.report_severity_level == "MEDIUM"


# ==========================================
# 4. TESTES DE DASHBOARD (Escrita Real no Disco)
# ==========================================

def test_dashboard_generation_real(dashboard_file):
    """
    Testa a função generate_dashboard escrevendo no disco.
    Cobre: Contagens, JSON dump, Template string e File Write.
    """
    plugin = Plugin()
    
    # Dados simulados (mas realistas)
    data = [
        {"severity": "high", "code": "B307", "file": "a.py"},
        {"severity": "high", "code": "B307", "file": "a.py"},
        {"severity": "medium", "code": "B105", "file": "b.py"}
    ]
    
    # Executa
    plugin.generate_dashboard(data)
    
    # Validações Físicas
    assert dashboard_file.exists()
    content = dashboard_file.read_text(encoding="utf-8")
    
    # Validações de Lógica (JSON injetado)
    assert '"total_issues": 3' in content
    assert '"total_files": 2' in content
    assert '"severity": "high"' in content
    assert '"count": 2' in content # 2 Highs
