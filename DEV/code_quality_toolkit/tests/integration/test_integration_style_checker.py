"""
Integration tests for the StyleChecker plugin (Task #215).
Verifica se o plugin deteta erros reais num fluxo de trabalho de integração.
"""

from toolkit.plugins.style_checker.plugin import Plugin


def test_integration_style_checker_detects_issues(tmp_path):
    """
    Test Integration: Verifica se o plugin analisa um ficheiro real e devolve erros.
    Não depende de Mocks.
    """
    # 1. Setup: Criar um ficheiro Python real com erros de estilo
    # Erro 1: Linha demasiado longa (>88 chars)
    # Erro 2: Nome de classe em snake_case (devia ser CamelCase)
    bad_code = (
        "class bad_naming_class:\n" 
        "    def foo(self):\n" 
        "        pass\n" 
        f"{'a' * 100}\n" # Linha com 100 chars
    )
    
    target_file = tmp_path / "bad_style.py"
    target_file.write_text(bad_code, encoding="utf-8")
    
    # 2. Executar o Plugin (Instância real)
    plugin = Plugin()
    # Ativar regra opcional para testar naming
    plugin.check_naming = True
    
    # A chamar o método analyze real
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    # 3. Assert (Verificar o Relatório Real)
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] >= 2
    
    results = report["results"]
    
    # Verificar erro de Naming
    naming_issue = next((r for r in results if r["code"] == "CLASS_NAMING"), None)
    assert naming_issue is not None
    assert naming_issue["line"] == 1
    
    # Verificar erro de Line Length
    length_issue = next((r for r in results if r["code"] == "LINE_LENGTH"), None)
    assert length_issue is not None
    assert "100" in length_issue["message"]


def test_integration_style_checker_clean_file(tmp_path):
    """
    Test Integration: Verifica se o plugin aceita um ficheiro limpo.
    """
    # 1. Setup
    clean_code = (
        "class GoodClass:\n"
        "    def good_method(self):\n"
        "        pass\n"
    )
    target_file = tmp_path / "good_style.py"
    target_file.write_text(clean_code, encoding="utf-8")
    
    # 2. Executar
    plugin = Plugin()
    report = plugin.analyze(target_file.read_text(encoding="utf-8"), str(target_file))
    
    # 3. Assert
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0