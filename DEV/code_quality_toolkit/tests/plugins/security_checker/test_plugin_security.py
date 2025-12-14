import pytest
import os
from pathlib import Path
from textwrap import dedent

# --- IMPORTS REAIS DO PROJETO ---
# Importamos o módulo para saber onde o ficheiro HTML vai parar
import src.toolkit.plugins.security_checker.plugin as plugin_module
from src.toolkit.plugins.security_checker.plugin import Plugin
from src.toolkit.utils.config import ToolkitConfig, PluginsConfig, SecurityCheckerConfig

# ==========================================
# 1. SETUP (FIXTURES)
# ==========================================

@pytest.fixture
def plugin():
    """Cria uma nova instância do plugin para cada teste."""
    return Plugin()

@pytest.fixture
def real_dashboard_path():
    """
    Gere o caminho do ficheiro REAL no disco.
    Apaga antes e depois do teste para não deixar lixo.
    """
    # Descobre a pasta onde está o plugin.py
    plugin_dir = Path(plugin_module.__file__).parent
    target_file = plugin_dir / "security_checker_dashboard.html"

    # Limpa antes de começar
    if target_file.exists():
        os.remove(target_file)
    
    yield target_file

    # Limpa depois de acabar
    if target_file.exists():
        os.remove(target_file)

# ==========================================
# 2. TESTES DE CONFIGURAÇÃO (SEM MOCKS)
# ==========================================

def test_config_loads_new_structure(plugin):
    """
    Teste Real: Cria os objetos de configuração reais e verifica se o plugin lê.
    """
    # 1. Criar a configuração como o Engine faria
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    full_config = ToolkitConfig(plugins=plugins_conf)
    
    # 2. Configurar
    plugin.configure(full_config)
    
    # 3. Verificar
    assert plugin.report_severity_level == "HIGH"

def test_config_defaults(plugin):
    """
    Teste Real: Se não passarmos nada, deve assumir o default (LOW).
    """
    empty_config = ToolkitConfig()
    plugin.configure(empty_config)
    
    assert plugin.report_severity_level == "LOW"

# ==========================================
# 3. TESTES DE ANÁLISE (REAL - BANDIT OU FALLBACK)
# Estes testes passam quer tenhas o Bandit instalado ou não,
# porque o teu código cobre os dois casos com a mesma lógica de deteção.
# ==========================================

def test_analyze_eval_detection(plugin):
    plugin.configure(ToolkitConfig())
    code = "eval('1+1')"
    
    # Executa a análise real
    report = plugin.analyze(code, "test_eval.py")
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 1
    
    # Verifica se o erro B307 (eval) foi encontrado
    codes = [i["code"] for i in report["results"]]
    assert "B307" in codes
    
    # Verifica se o nome do ficheiro foi injetado corretamente (Fix do Engine)
    assert report["results"][0]["file"] == "test_eval.py"

def test_analyze_hardcoded_password(plugin):
    plugin.configure(ToolkitConfig())
    code = "PASSWORD = 'secret'"
    
    report = plugin.analyze(code, "auth.py")
    
    assert report["summary"]["issues_found"] >= 1
    codes = [i["code"] for i in report["results"]]
    assert "B105" in codes

def test_analyze_sql_injection(plugin):
    plugin.configure(ToolkitConfig())
    # Query insegura
    code = "cursor.execute('SELECT * FROM %s' % table)"
    
    report = plugin.analyze(code, "db.py")
    
    assert report["summary"]["issues_found"] >= 1
    codes = [i["code"] for i in report["results"]]
    
    # Aceita qualquer um destes códigos (dependendo se corre Bandit ou Fallback)
    assert any(c in codes for c in ["B601", "B606", "B608"])

def test_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "SecurityChecker"
    assert "version" in meta

# ==========================================
# 4. TESTES DO DASHBOARD (REAL I/O NO DISCO)
# ==========================================

def test_generate_dashboard_creates_file(plugin, real_dashboard_path):
    """
    Teste de Integração:
    1. Passa dados.
    2. O Plugin escreve o ficheiro HTML no disco.
    3. Nós lemos o ficheiro e validamos o conteúdo.
    """
    # Dados para o relatório
    data = [
        {"severity": "high", "code": "B307", "file": "login.py"},
        {"severity": "low", "code": "B105", "file": "config.py"}
    ]

    # Executa (Escreve no disco)
    plugin.generate_dashboard(data)

    # Verifica se existe
    assert real_dashboard_path.exists(), "O ficheiro HTML não foi criado!"
    assert real_dashboard_path.stat().st_size > 0

    # Verifica conteúdo
    content = real_dashboard_path.read_text(encoding="utf-8")
    
    # Valida JSON injetado
    assert '"total_issues": 2' in content
    assert '"file": "login.py"' in content
    assert '"severity": "high"' in content
    
    # Valida HTML
    assert "SecurityChecker Dashboard" in content

def test_generate_dashboard_empty(plugin, real_dashboard_path):
    """
    Teste Real: Gera dashboard com lista vazia.
    """
    plugin.generate_dashboard([])

    assert real_dashboard_path.exists()
    content = real_dashboard_path.read_text(encoding="utf-8")
    
    assert '"total_issues": 0' in content
    assert '"top_files": []' in content