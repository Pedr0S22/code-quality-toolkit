from textwrap import dedent
from pathlib import Path

from toolkit.plugins.security_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


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

def test_security_checker_loads_config_correctly():
        """
        Verifica se o plugin lê 'report_severity_level' corretamente.
        """
        plugin = Plugin()
        full_config = ToolkitConfig()

        # Vrificamos se o default config é realmente "LOW"
        plugin.configure(full_config)
        assert plugin.report_severity_level == "LOW"


        assert plugin.report_severity_level == "LOW"


def test_generate_dashboard_real_execution(tmp_path: Path):
    """
    Testa a geração do dashboard, garantindo cobertura para agregação (aggregate_data)
    e escrita do arquivo HTML.
    """
    plugin = Plugin()
    
    # 1. Simulação dos resultados agregados (mínimo necessário para o dashboard)
    # A estrutura deve espelhar a saída do Engine com resultados de vários arquivos
    aggregated_results = [
        {
            "file": "file_a.py",
            "plugins": [{
                "plugin": "SecurityChecker",
                "results": [
                    {"severity": "high", "code": "B307", "message": "eval", "file": "file_a.py"},
                    {"severity": "low", "code": "B105", "message": "pwd", "file": "file_a.py"},
                ]
            }]
        },
        {
            "file": "file_b.py",
            "plugins": [{
                "plugin": "SecurityChecker",
                "results": [
                    {"severity": "medium", "code": "B601", "message": "os.system", "file": "file_b.py"},
                ]
            }]
        },
    ]

    output_file = tmp_path / "security_checker_dashboard.html"
    
    # 2. Execução da Geração do Dashboard
    output_path_str = plugin.generate_dashboard(aggregated_results, str(output_file))
    
    # 3. Verificação
    assert output_path_str == str(output_file.absolute())
    assert output_file.exists()
    
    # Verifica o conteúdo mínimo
    content = output_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "SecurityChecker Dashboard" in content
    assert "Issues by Severity" in content # Confirma que o template D3 foi processado