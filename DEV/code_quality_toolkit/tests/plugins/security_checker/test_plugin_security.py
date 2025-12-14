import pytest
import os
import json
import re
from pathlib import Path
from textwrap import dedent

# --- IMPORTS REAIS ---
import src.toolkit.plugins.security_checker.plugin as plugin_module
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
def plugin():
    return Plugin()

@pytest.fixture
def dashboard_file():
    """Gere o ficheiro real no disco."""
    plugin_dir = Path(plugin_module.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    if target_file.exists(): os.remove(target_file)
    yield target_file
    if target_file.exists(): os.remove(target_file)

def extract_data_from_html(html_content):
    """
    Extrai o objeto JSON real que foi injetado no HTML.
    Procura por: const data = { ... };
    """
    # Regex para capturar o JSON entre "const data = " e ";"
    match = re.search(r'const data = ({.*?});', html_content, re.DOTALL)
    if not match:
        raise ValueError("JSON de dados não encontrado no HTML gerado!")
    
    return json.loads(match.group(1))

# ==========================================
# 2. TESTES DE LÓGICA DO DASHBOARD (REAL)
# ==========================================

def test_dashboard_logic_aggregation(plugin, dashboard_file):
    """
    Testa se a matemática de contagem de severidades está certa.
    """
    # 1. Dados de entrada (Lista Plana)
    raw_data = [
        {"severity": "high", "file": "a.py"},
        {"severity": "high", "file": "b.py"},
        {"severity": "medium", "file": "c.py"},
        {"severity": "low", "file": "d.py"},
        {"severity": "info", "file": "e.py"}
    ]

    # 2. Executar (Escreve no disco)
    plugin.generate_dashboard(raw_data)

    # 3. Ler e Extrair Dados
    assert dashboard_file.exists()
    content = dashboard_file.read_text(encoding="utf-8")
    data = extract_data_from_html(content)

    # 4. Validar Lógica
    # Total Issues
    assert data["metrics"]["total_issues"] == 5
    
    # Contagem de High
    high_obj = next(x for x in data["severity_counts"] if x["severity"] == "high")
    assert high_obj["count"] == 2
    
    # Contagem de Medium
    med_obj = next(x for x in data["severity_counts"] if x["severity"] == "medium")
    assert med_obj["count"] == 1

def test_dashboard_logic_sorting_top_files(plugin, dashboard_file):
    """
    Testa se a lógica de ordenação (Top Files) funciona corretamente.
    O ficheiro com mais erros deve aparecer primeiro.
    """
    raw_data = [
        {"file": "pior.py", "severity": "high"},
        {"file": "pior.py", "severity": "low"},   # pior.py = 2 erros
        {"file": "medio.py", "severity": "high"}, # medio.py = 1 erro
    ]

    plugin.generate_dashboard(raw_data)

    content = dashboard_file.read_text(encoding="utf-8")
    data = extract_data_from_html(content)

    # Valida Top Files
    top_files = data["top_files"]
    
    # O primeiro deve ser o "pior.py" com 2
    assert top_files[0]["file"] == "pior.py"
    assert top_files[0]["count"] == 2
    
    # O segundo deve ser "medio.py" com 1
    assert top_files[1]["file"] == "medio.py"
    assert top_files[1]["count"] == 1

def test_dashboard_logic_defaults(plugin, dashboard_file):
    """
    Testa se a lógica lida com dados incompletos sem crashar.
    """
    # Dados sem 'file' e sem 'severity'
    raw_data = [{"code": "B101"}] 

    plugin.generate_dashboard(raw_data)

    content = dashboard_file.read_text(encoding="utf-8")
    data = extract_data_from_html(content)

    # Deve ter usado 'unknown' para ficheiro
    assert data["top_files"][0]["file"] == "unknown"
    
    # Deve ter usado 'info' para severidade
    info_obj = next(x for x in data["severity_counts"] if x["severity"] == "info")
    assert info_obj["count"] == 1

# ==========================================
# 3. TESTES DE CONFIGURAÇÃO (REAL)
# ==========================================

def test_config_loading_real(plugin):
    """Testa leitura da configuração nova."""
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    full_conf = ToolkitConfig(plugins=PluginsConfig(security_checker=sec_conf))
    
    plugin.configure(full_conf)
    
    assert plugin.report_severity_level == "HIGH"

def test_config_defaults_real(plugin):
    """Testa default."""
    plugin.configure(ToolkitConfig())
    assert plugin.report_severity_level == "LOW"

# ==========================================
# 4. TESTES DE ANÁLISE (REAL - BANDIT)
# ==========================================

def test_analyze_real_eval(plugin):
    """Testa deteção real do Bandit (Eval)."""
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("eval('1+1')", "eval_test.py")
    
    assert report["summary"]["issues_found"] >= 1
    codes = [i["code"] for i in report["results"]]
    assert "B307" in codes
    assert report["results"][0]["file"] == "eval_test.py"

def test_analyze_real_sql(plugin):
    """Testa deteção real do Bandit (SQL)."""
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("cursor.execute('SELECT * FROM %s' % x)", "sql.py")
    
    assert report["summary"]["issues_found"] >= 1
    codes = [i["code"] for i in report["results"]]
    # Bandit pode retornar B601 ou B608
    assert any(c in codes for c in ["B601", "B608", "B606"])

def test_analyze_clean_code(plugin):
    """Testa código seguro."""
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("print('Hello')", "clean.py")
    
    assert report["summary"]["issues_found"] == 0