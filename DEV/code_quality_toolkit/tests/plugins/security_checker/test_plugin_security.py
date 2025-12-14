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


def test_analyze_is_working():
    """Teste básico: O plugin consegue encontrar um 'eval'?"""
    plugin = Plugin()
    # Configuração vazia (usa defaults)
    plugin.configure(ToolkitConfig())

    code = "eval('1+1')"
    report = plugin.analyze(code, "basic_test.py")

    # Se encontrar issues, o código foi executado -> Coverage aumenta
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1
    assert report["results"][0]["file"] == "basic_test.py"


def test_analyze_is_safe():
    """Teste básico: Ficheiro sem erros não crasha?"""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    report = plugin.analyze("print('Ola')", "clean.py")
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0


def test_configuration_loading():
    """Teste básico: O plugin lê a configuração HIGH?"""
    plugin = Plugin()
    
    # Criar config real
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    config = ToolkitConfig(plugins=plugins_conf)
    
    plugin.configure(config)
    
    assert plugin.report_severity_level == "HIGH"


def test_dashboard_file_creation():
    """
    Teste básico: O plugin cria o ficheiro HTML?
    Sem mocks. Escreve, vê se existe, apaga.
    """
    plugin = Plugin()
    
    # 1. Descobrir onde o ficheiro vai parar
    # Usamos o caminho do módulo importado para garantir que estamos na mesma pasta
    import src.toolkit.plugins.security_checker.plugin as p_mod
    plugin_dir = Path(p_mod.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    # Limpar antes (caso tenha sobrado de antes)
    if target_file.exists():
        os.remove(target_file)

    try:
        # 2. Gerar
        data = [{"severity": "high", "code": "B307", "file": "test.py"}]
        plugin.generate_dashboard(data)

        # 3. Validar
        assert target_file.exists()
        assert target_file.stat().st_size > 0
        
        # Validar conteúdo simples
        content = target_file.read_text(encoding="utf-8")
        assert "SecurityChecker" in content

    finally:
        # 4. Limpar depois
        if target_file.exists():
            os.remove(target_file)
