from pathlib import Path
from textwrap import dedent

from toolkit.plugins.security_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


class MockRules:
    """Simula a secção config.rules com o atributo de severidade."""
    def __init__(self, severity):
        self.security_report_level = severity

class MockToolkitConfig:
    """Simula o objeto ToolkitConfig que o plugin lê."""
    def __init__(self, severity="LOW"):
        # O plugin SecurityChecker lê de config.rules
        self.rules = MockRules(severity)

    @property
    def plugins(self):
        return None

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

# ======================================================================
# NOVOS TESTES PARA AUMENTAR COBERTURA
# ======================================================================

def test_analyze_no_issues_found() -> None:
    """Verifica o fluxo de retorno de 0 issues (completed) pelo Bandit."""
    code = "def my_safe_function(x): return x + 1"
    plugin = Plugin()
    plugin.configure(MockToolkitConfig(severity="HIGH"))
    report = plugin.analyze(code, "safe.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
    assert report["results"] == []

def test_analyze_empty_code() -> None:
    """Verifica a análise com string de código vazia."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig(severity="LOW"))
    report = plugin.analyze("", "empty.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0

def test_configuration_no_rules_section() -> None:
    """Cobre o caso em que 'config.rules' é None ou não tem o atributo."""
    
    # 1. Simula config.rules = None
    class MockNoRules:
        rules = None 
    
    plugin_a = Plugin()
    plugin_a.configure(MockNoRules())
    # Deve manter o default
    assert plugin_a.report_severity_level == "LOW"

    # 2. Simula rules sem o atributo security_report_level
    class MockRulesMissingAttr:
        def __init__(self):
            # O atributo existe, mas está vazio
            pass 
    class MockConfigMissingAttr:
        rules = MockRulesMissingAttr()
        @property
        def plugins(self):
            return None

    plugin_b = Plugin()
    plugin_b.configure(MockConfigMissingAttr())
    # Deve manter o default
    assert plugin_b.report_severity_level == "LOW"


def test_aggregate_data_for_dashboard_empty_results() -> None:
    """Cobre o fluxo de agregação com lista de resultados vazia."""
    plugin = Plugin()
    aggregated = plugin._aggregate_data_for_dashboard([])

    assert aggregated["metrics"]["total_files"] == 0
    assert aggregated["metrics"]["total_issues"] == 0
    assert aggregated["severity_counts"] == []
    assert aggregated["rule_counts"] == []
    assert aggregated["top_files"] == []

def test_aggregate_data_for_dashboard_flat_format() -> None:
    """
    Cobre o fluxo de agregação de resultados 'flat' (sem aninhamento de plugins),
    garantindo a compatibilidade.
    """
    plugin = Plugin()
    flat_results = [
        {"severity": "medium", "code": "B100", "file": "f1.py", "line": 1},
        {"severity": "low", "code": "B100", "file": "f2.py", "line": 1},
        # Issue com severidade desconhecida (deve virar 'info')
        {"severity": "unknown_sev", "code": "UNKNOWN", "file": "f3.py", "line": 1},
    ]

    aggregated = plugin._aggregate_data_for_dashboard(flat_results)

    assert aggregated["metrics"]["total_issues"] == 3
    assert aggregated["metrics"]["total_files"] == 3
    
    # Verifica a contagem de regras UNKNOWN e info
    assert any(d["severity"] == "info" for d in aggregated["severity_counts"])
    assert any(d["code"] == "UNKNOWN" for d in aggregated["rule_counts"])

def test_aggregate_data_top_files_limit() -> None:
    """
    Cobre a lógica de limite do top_files (deve ser 10) e a contagem.
    """
    plugin = Plugin()
    # 12 issues em arquivos diferentes
    many_files = []
    for i in range(12):
        issue_data = {
            "severity": "high",
            "code": "B307", 
            "message": "eval", 
            "file": f"file_{i}.py", 
            "line": 1
        }
        # Simula o formato aninhado
        many_files.append({
            "file": f"file_{i}.py",
            "plugins": [{
                "plugin": "SecurityChecker",
                "results": [issue_data]
            }]
        })

    aggregated = plugin._aggregate_data_for_dashboard(many_files)
    
    # total_files deve ser 12 (todos únicos)
    assert aggregated["metrics"]["total_files"] == 12 
    
    # top_files deve ser limitado a 10
    assert len(aggregated["top_files"]) == 10
    
    # Garante que o primeiro arquivo na lista ainda é file_0.py
    assert aggregated["top_files"][0]["file"] == "file_0.py"

def test_analyze_exception_handling(monkeypatch) -> None:
    """
    Cobre o bloco 'except Exception as e' no método analyze,
    forçando uma falha interna controlada.
    """
    plugin = Plugin()

    # 1. Função que substitui o Bandit.run_tests e lança um erro
    def always_fail_run_tests(self):
        # Aumentamos a complexidade do erro para garantir que é o nosso
        raise RuntimeError("Simulated internal Bandit failure for coverage")

    # 2. Injeta a função de falha no BanditManager
    from toolkit.plugins.security_checker.plugin import BanditManager
    monkeypatch.setattr(BanditManager, "run_tests", always_fail_run_tests)

    code = "print('safe code')"
    report = plugin.analyze(code, "fail_test.py")

    # Esperamos que o bloco 'except' seja executado
    assert report["summary"]["status"] == "failed"
    # Linha quebrada para evitar E501
    assert "Erro SecurityChecker: Simulated internal Bandit failure" in \
           report["summary"]["error"]
    assert report["summary"]["issues_found"] == 0


def test_generate_dashboard_exception_handling(tmp_path: Path) -> None:
    """
    Cobre o bloco 'except Exception as e' no método generate_dashboard,
    forçando uma falha de I/O ao tentar escrever em um diretório.
    """
    plugin = Plugin()

    # Simulação mínima de resultados
    aggregated_results = [{
        "file": "f.py",
        "plugins": [{
            "plugin": "SecurityChecker",
            "results": [
                {
                    "severity": "high", "code": "B307",
                    "message": "x", "file": "f.py", "line": 1
                }
            ]
        }]
    }]

    # Usamos o caminho de um diretório (tmp_path), o que forçará o erro
    output_path = plugin.generate_dashboard(aggregated_results, str(tmp_path))

    # Esperamos que a função retorne uma string vazia em caso de falha
    assert output_path == ""