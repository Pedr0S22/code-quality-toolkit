"""
Integration tests for the StyleChecker plugin (Task #215).
"""

from pathlib import Path
from toolkit.plugins.style_checker.plugin import Plugin

def test_integration_style_checker_detects_issues(tmp_path):
    """
    Test Integration: Verifica se o plugin analisa um ficheiro real e devolve erros.
    """
    # 1. Setup: Criar um ficheiro Python real com erros
    bad_code = (
        "class bad_naming_class:\n" 
        "    def foo(self):\n" 
        "        pass\n" 
        f"{'a' * 100}\n"
    )
    
    target_file = tmp_path / "bad_style.py"
    target_file.write_text(bad_code, encoding="utf-8")
    
    # 2. Executar o Plugin
    plugin = Plugin()
    
    # --- CORREÇÃO AQUI ---
    # Temos de ativar a verificação de nomes, pois por defeito é False
    plugin.check_naming = True 
    # ---------------------

    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    # 3. Assert
    assert report["summary"]["status"] == "completed"
    # Agora deve encontrar 2 (Line Length + Naming)
    assert report["summary"]["issues_found"] >= 2
    
    results = report["results"]
    naming_issue = next((r for r in results if r["code"] == "CLASS_NAMING"), None)
    assert naming_issue is not None

def test_integration_style_checker_clean_file(tmp_path):
    """
    Test Integration: Verifica se o plugin aceita um ficheiro limpo.
    """
    clean_code = "class GoodClass:\n    pass\n"
    target_file = tmp_path / "good_style.py"
    target_file.write_text(clean_code, encoding="utf-8")
    
    plugin = Plugin()
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    assert report["summary"]["issues_found"] == 0