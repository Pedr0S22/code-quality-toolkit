from textwrap import dedent

from toolkit.plugins.security_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig

import os
import pytest
from pathlib import Path

# Precisamos disto para localizar a pasta do dashboard
import src.toolkit.plugins.security_checker.plugin as plugin_module
# Precisamos disto para criar a configuração real
from src.toolkit.utils.config import PluginsConfig, SecurityCheckerConfig

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


def real_dashboard_path():
    """
    Fixture que gere o ficheiro REAL no disco.
    1. Descobre onde o plugin guarda o HTML.
    2. Apaga antes do teste (para garantir limpeza).
    3. Apaga depois do teste (para não deixar lixo).
    """
    # Descobre a pasta onde está o plugin.py
    plugin_dir = Path(plugin_module.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    # Limpeza Inicial
    if target_file.exists():
        os.remove(target_file)
    
    yield target_file

    # Limpeza Final
    if target_file.exists():
        os.remove(target_file)


def test_config_loads_new_structure_real():
    """
    Teste 100% Real: Instancia as classes de configuração verdadeiras
    e verifica se o plugin as lê corretamente.
    """
    plugin = Plugin()
    
    # Criar a configuração REAL (sem mocks)
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    full_config = ToolkitConfig(plugins=plugins_conf)
    
    # Injetar no plugin
    plugin.configure(full_config)
    
    # Verificar
    assert plugin.report_severity_level == "HIGH"


def test_config_defaults_real():
    """Teste Real: Verifica o comportamento padrão (LOW)."""
    plugin = Plugin()
    empty_config = ToolkitConfig() # Config vazia
    
    plugin.configure(empty_config)
    
    assert plugin.report_severity_level == "LOW"


def test_generate_dashboard_real_file(real_dashboard_path):
    """
    Teste de Integração Real:
    1. O Plugin escreve o ficheiro HTML no seu disco rígido.
    2. Nós lemos o ficheiro do disco.
    3. Validamos se o conteúdo está lá.
    """
    plugin = Plugin()
    
    # Dados para o relatório
    data = [
        {"severity": "high", "code": "B307", "file": "login.py"},
        {"severity": "medium", "code": "B105", "file": "config.py"}
    ]

    # AÇÃO: Escrever no disco
    plugin.generate_dashboard(data)

    # VERIFICAÇÃO 1: O ficheiro existe fisicamente?
    assert real_dashboard_path.exists(), "O ficheiro HTML não foi criado!"
    assert real_dashboard_path.stat().st_size > 0

    # VERIFICAÇÃO 2: Ler o conteúdo
    content = real_dashboard_path.read_text(encoding="utf-8")
    
    # Validar se o JSON foi injetado corretamente
    assert '"total_issues": 2' in content
    assert '"file": "login.py"' in content
    assert '"severity": "high"' in content
    
    # Validar se o HTML tem o título certo
    assert "SecurityChecker Analysis" in content


def test_generate_dashboard_empty_real(real_dashboard_path):
    """Teste Real: Gera dashboard com lista vazia."""
    plugin = Plugin()
    plugin.generate_dashboard([])

    assert real_dashboard_path.exists()
    content = real_dashboard_path.read_text(encoding="utf-8")
    
    assert '"total_issues": 0' in content
    assert '"top_files": []' in content