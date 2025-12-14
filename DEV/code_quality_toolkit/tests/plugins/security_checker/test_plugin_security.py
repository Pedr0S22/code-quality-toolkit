from textwrap import dedent

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



def test_security_checker_detects_subprocess_shell_true() -> None:
    """Deteta shell=True em subprocess (B602)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = dedent("""
        import subprocess
        def run(cmd):
            # shell=True permite injeção de comandos
            subprocess.call(cmd, shell=True)
    """)
    report = plugin.analyze(code, "shell_test.py")
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_bind_all_interfaces() -> None:
    """Deteta binding para 0.0.0.0 (B104)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = dedent("""
        def start_server():
            # Expor para a web inteira é mau
            s.bind('0.0.0.0')
    """)
    report = plugin.analyze(code, "network_test.py")
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_assert_in_code() -> None:
    """Deteta uso de assert em lógica de negócio (B101)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "assert user.is_admin, 'User must be admin'"
    report = plugin.analyze(code, "logic_test.py")
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_random_usage() -> None:
    """Deteta uso de random para segurança (B311)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = dedent("""
        import random
        def generate_token():
            return random.random()
    """)
    report = plugin.analyze(code, "token_test.py")
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_insecure_temp_file() -> None:
    """Deteta criação de ficheiros em /tmp (B108)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    code = "f = open('/tmp/tempfile', 'w')"
    report = plugin.analyze(code, "file_test.py")
    assert report["summary"]["issues_found"] >= 1