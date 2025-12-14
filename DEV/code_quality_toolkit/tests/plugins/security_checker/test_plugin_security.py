import os
import pytest
import json
from pathlib import Path
from textwrap import dedent

# Imports do Projeto
from src.toolkit.plugins.security_checker.plugin import Plugin
from src.toolkit.utils.config import ToolkitConfig

# ==============================================================================
# TESTES ORIGINAIS (MANTIDOS)
# ==============================================================================

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

# ==============================================================================
# NOVOS TESTES DE SEGURANÇA ADICIONADOS
# ==============================================================================

def test_security_checker_detects_unsafe_yaml_load() -> None:
    """Testa deteção de deserialização insegura com YAML (B506)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        import yaml
        def load_config(data):
            # yaml.load sem Loader seguro é perigoso
            return yaml.load(data)
        """
    )
    report = plugin.analyze(code, "yaml_test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_subprocess_shell_true() -> None:
    """Testa uso de shell=True em subprocess (B602)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        import subprocess
        def run_cmd(cmd):
            # shell=True é vetor de injeção
            subprocess.call(cmd, shell=True)
        """
    )
    report = plugin.analyze(code, "subprocess_test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_bind_all_interfaces() -> None:
    """Testa binding em 0.0.0.0 (B104)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        def run_server():
            # Expor para 0.0.0.0 é risco de segurança
            app.run(host='0.0.0.0')
        """
    )
    report = plugin.analyze(code, "server.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_assert_usage() -> None:
    """Testa uso de assert em código de produção (B101)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        def login(user):
            # Asserts são removidos se correr com python -O
            assert user.is_admin
            grant_access()
        """
    )
    report = plugin.analyze(code, "logic.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_pseudo_random() -> None:
    """Testa uso de random para fins criptográficos (B311)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        import random
        def gen_token():
            return random.random()
        """
    )
    report = plugin.analyze(code, "token.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1

def test_security_checker_detects_hardcoded_tmp_directory() -> None:
    """Testa uso de diretórios temporários inseguros (B108)."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    code = dedent(
        """
        def save_temp(data):
            with open('/tmp/tempfile', 'w') as f:
                f.write(data)
        """
    )
    report = plugin.analyze(code, "file_ops.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1