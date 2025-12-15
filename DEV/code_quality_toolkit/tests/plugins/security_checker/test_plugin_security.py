import pytest
import os
from pathlib import Path
from textwrap import dedent

# --- A CORREÇÃO CRÍTICA DOS IMPORTS ---
# Usamos 'toolkit' direto, sem 'src'. Isso alinha com o pip install -e .
from toolkit.plugins.security_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig, PluginsConfig, SecurityCheckerConfig

# ==============================================================================
# TESTES DE INTEGRAÇÃO (USANDO FICHEIROS REAIS - tmp_path)
# ==============================================================================

def test_security_checker_detects_real_issues_in_file(tmp_path):
    """
    Simula um ficheiro real no disco e corre o Bandit nele.
    """
    # 1. Criar ficheiro numa pasta temporária isolada
    unsafe_code = (
        "import os\n"
        "eval('1+1')\n"           # B307
        "PASSWORD = '123'\n"      # B105
    )
    
    target_file = tmp_path / "vulnerable.py"
    target_file.write_text(unsafe_code, encoding="utf-8")

    # 2. Configurar Plugin
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    # 3. Analisar (Lendo do disco)
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))

    # 4. Validar
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 2
    
    found_codes = [i["code"] for i in report["results"]]
    assert "B307" in found_codes
    assert "B105" in found_codes
    
    # Verifica se o nome do ficheiro veio correto
    assert report["results"][0]["file"] == str(target_file)


def test_security_checker_clean_file(tmp_path):
    """Verifica comportamento com ficheiro limpo."""
    clean_code = "print('Hello World')\n"
    target_file = tmp_path / "clean.py"
    target_file.write_text(clean_code, encoding="utf-8")
    
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0


def test_security_checker_sql_injection(tmp_path):
    """Teste específico para SQL."""
    sql_code = "cursor.execute('SELECT * FROM users WHERE name = ' + user_input)"
    target_file = tmp_path / "sql.py"
    target_file.write_text(sql_code, encoding="utf-8")
    
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    assert report["summary"]["issues_found"] >= 1


# ==============================================================================
# TESTES DE CONFIGURAÇÃO (COBRE O MÉTODO configure)
# ==============================================================================

def test_configure_respects_high_severity():
    plugin = Plugin()
    
    # Configuração Real
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    full_config = ToolkitConfig(plugins=plugins_conf)
    
    plugin.configure(full_config)
    
    assert plugin.report_severity_level == "HIGH"


def test_configure_defaults():
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    assert plugin.report_severity_level == "LOW"


# ==============================================================================
# TESTE DE DASHBOARD (REQUISITO PARA COVERAGE)
# Este teste cria o ficheiro, confirma que existe e apaga logo a seguir.
# ==============================================================================

def test_generate_dashboard_real_execution():
    plugin = Plugin()
    data = [{"severity": "high", "code": "B307", "file": "test.py"}]
    
    # 1. Executa (Vai criar o ficheiro na pasta source real)
    plugin.generate_dashboard(data)
    
    # 2. Descobre onde ele está (Lógica interna do plugin)
    # Precisamos importar o módulo para saber o caminho __file__
    import toolkit.plugins.security_checker.plugin as p_mod
    
    target_file = Path(p_mod.__file__).parent / "security_checker_dashboard.html"
    
    try:
        # 3. Valida se foi criado
        assert target_file.exists()
        assert target_file.stat().st_size > 0
        
        content = target_file.read_text(encoding="utf-8")
        assert "SecurityChecker" in content
        
    finally:
        # 4. Limpeza (Obrigatório)
        if target_file.exists():
            os.remove(target_file)