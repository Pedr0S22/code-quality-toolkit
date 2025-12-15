import pytest
import os
from pathlib import Path

# Importação direta (ajustada para a tua estrutura de pastas)
from src.toolkit.plugins.security_checker.plugin import Plugin
from src.toolkit.utils.config import ToolkitConfig, PluginsConfig, SecurityCheckerConfig

# ==============================================================================
# 1. TESTES DE INTEGRAÇÃO (USANDO FICHEIROS REAIS - tmp_path)
# Inspirado em: tests/integration/test_integration_style_checker.py
# ==============================================================================

def test_security_checker_detects_real_issues_in_file(tmp_path):
    """
    Cria um ficheiro Python real com código perigoso numa pasta temporária,
    analisa-o e verifica se o Bandit encontrou os erros.
    """
    # 1. Setup: Criar ficheiro com vulnerabilidades reais
    unsafe_code = (
        "import os\n"
        "import pickle\n"
        "eval('1+1')\n"           # B307: Eval
        "PASSWORD = '123'\n"      # B105: Password
        "pickle.load(f)\n"        # B301: Pickle
    )
    
    target_file = tmp_path / "vulnerable.py"
    target_file.write_text(unsafe_code, encoding="utf-8")

    # 2. Executar o Plugin
    plugin = Plugin()
    # Configuração básica
    plugin.configure(ToolkitConfig())

    # Lemos o conteúdo do ficheiro real e passamos o caminho real
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))

    # 3. Assert (Validações)
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 3
    
    # Verificar se os códigos específicos do Bandit estão lá
    found_codes = [issue["code"] for issue in report["results"]]
    assert "B307" in found_codes  # Eval
    assert "B105" in found_codes  # Password
    assert "B301" in found_codes  # Pickle
    
    # Verificar se o caminho do ficheiro está correto no relatório
    assert report["results"][0]["file"] == str(target_file)


def test_security_checker_clean_file(tmp_path):
    """
    Verifica se o plugin aceita um ficheiro limpo sem dar falso positivo.
    """
    clean_code = "print('Hello World')\n"
    target_file = tmp_path / "clean.py"
    target_file.write_text(clean_code, encoding="utf-8")
    
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0


def test_security_checker_sql_injection_file(tmp_path):
    """
    Teste específico para SQL Injection num ficheiro real.
    """
    sql_code = "cursor.execute('SELECT * FROM users WHERE name = ' + user_input)"
    target_file = tmp_path / "sql_test.py"
    target_file.write_text(sql_code, encoding="utf-8")
    
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    assert report["summary"]["issues_found"] >= 1
    # Verifica se encontrou B601 (Injection) ou B608 (Hardcoded SQL)
    found_codes = [issue["code"] for issue in report["results"]]
    assert any(c in found_codes for c in ["B601", "B608", "B606"])


# ==============================================================================
# 2. TESTES DE CONFIGURAÇÃO (LÓGICA INTERNA)
# Necessário para cobrir o método 'configure' do plugin.py
# ==============================================================================

def test_configure_respects_high_severity():
    """
    Verifica se o método configure lê corretamente a estrutura de classes.
    """
    plugin = Plugin()
    
    # Simula a estrutura exata que o Engine passa
    sec_conf = SecurityCheckerConfig(report_severity_level="HIGH")
    plugins_conf = PluginsConfig(security_checker=sec_conf)
    full_config = ToolkitConfig(plugins=plugins_conf)
    
    plugin.configure(full_config)
    
    assert plugin.report_severity_level == "HIGH"


def test_configure_defaults_to_low():
    """
    Verifica o comportamento padrão.
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig()) # Config vazia
    assert plugin.report_severity_level == "LOW"


# ==============================================================================
# 3. TESTE DE DASHBOARD SIMPLES (PARA COVERAGE)
# O método generate_dashboard é parte do ficheiro, tem de ser testado.
# ==============================================================================

def test_generate_dashboard_creates_file():
    """
    Testa se o método gera o ficheiro HTML no disco.
    Simples: Executa -> Verifica -> Apaga.
    """
    plugin = Plugin()
    
    # Dados fictícios
    data = [{"severity": "high", "code": "B307", "file": "test.py"}]
    
    # 1. Executar
    plugin.generate_dashboard(data)
    
    # 2. Verificar onde foi criado
    # (O plugin usa Path(__file__).parent internamente)
    import src.toolkit.plugins.security_checker.plugin as p_mod
    expected_file = Path(p_mod.__file__).parent / "security_checker_dashboard.html"
    
    assert expected_file.exists()
    assert expected_file.stat().st_size > 0
    
    # 3. Limpar
    if expected_file.exists():
        os.remove(expected_file)