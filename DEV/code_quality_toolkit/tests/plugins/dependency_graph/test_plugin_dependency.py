from textwrap import dedent

# Importa a classe do teu plugin
from toolkit.plugins.dependency_graph.plugin import Plugin


# --- Teste G: Contrato e Metadados ---
def test_plugin_metadata():
    """
    Critério G: Verifica se o plugin se identifica corretamente (nome, versão, descrição).
    """
    plugin = Plugin()
    metadata = plugin.get_metadata()
    
    assert metadata["name"] == "DependencyGraph"
    assert "version" in metadata
    assert "description" in metadata

def test_analyze_returns_valid_json_structure():
    """
    Critério G: Verifica se o output segue a estrutura JSON obrigatória (results, summary).
    """
    plugin = Plugin()
    # Executa com um código simples para garantir sucesso
    report = plugin.analyze("import os", "test.py")
    
    assert "results" in report
    assert "summary" in report
    assert "status" in report["summary"]
    assert report["summary"]["status"] == "completed"
    
    # Verifica se o sumário tem os campos específicos deste plugin
    assert "stdlib_count" in report["summary"]
    assert "dependency_graph" in report["summary"]

# --- Testes A, B, C: Lógica de Parsing (AST) ---

def test_analyze_simple_import():
    """
    Critério A: Testa 'import modulo' e múltiplos imports na mesma linha.
    """
    plugin = Plugin()
    code = dedent("""
        import os
        import sys, json
    """)
    
    report = plugin.analyze(code, "test.py")
    results = report["results"]
    
    # Deve encontrar 3 imports: os, sys, json
    assert len(results) == 3
    messages = [r["message"] for r in results]
    
    # O teu plugin gera mensagens como "Importa módulo 'os'..."
    assert any("Importa módulo 'os'" in m for m in messages)
    assert any("Importa módulo 'sys'" in m for m in messages)
    assert any("Importa módulo 'json'" in m for m in messages)

def test_analyze_from_import():
    """
    Critério B: Testa 'from pacote import modulo'.
    """
    plugin = Plugin()
    code = dedent("""
        from typing import List, Dict
        from datetime import datetime
    """)
    
    report = plugin.analyze(code, "test.py")
    results = report["results"]
    
    messages = [r["message"] for r in results]
    
    # Deve identificar a origem e o nome importado
    # Ex: "Importa 'List' de 'typing'"
    assert any("Importa 'List' de 'typing'" in m for m in messages)
    assert any("Importa 'Dict' de 'typing'" in m for m in messages)
    assert any("Importa 'datetime' de 'datetime'" in m for m in messages)

def test_analyze_nested_import():
    """
    Critério C: Testa imports dentro de funções (escopo local).
    """
    plugin = Plugin()
    code = dedent("""
        def minha_funcao():
            import math
            return math.pi
    """)
    
    report = plugin.analyze(code, "test.py")
    results = report["results"]
    
    # O parser AST deve encontrar mesmo estando indentado
    assert len(results) == 1
    assert "Importa módulo 'math'" in results[0]["message"]
    # A linha deve ser > 1 (porque está dentro da função)
    assert results[0]["line"] > 1

# --- Testes D, E, F: Casos Limite ---

def test_analyze_empty_file():
    """
    Critério D: Ficheiro vazio não deve crashar e deve retornar 0 resultados.
    """
    plugin = Plugin()
    report = plugin.analyze("", "empty.py")
    
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0

def test_analyze_syntax_error():
    """
    Critério E: Ficheiro com erro de sintaxe.
    O plugin deve falhar graciosamente ("failed") e reportar o erro DEP-SYNTAX.
    """
    plugin = Plugin()
    # Código inválido (falta fechar parênteses)
    code = "import os\ndef funcao_quebrada(" 
    
    report = plugin.analyze(code, "broken.py")
    
    # Verifica o comportamento definido no teu código:
    assert report["summary"]["status"] == "failed"
    assert report["summary"]["issues_found"] == 1
    
    issue = report["results"][0]
    assert issue["code"] == "DEP-SYNTAX"
    assert "Erro de sintaxe" in issue["message"]

def test_analyze_import_star():
    """
    Critério F: Testa 'from modulo import *'.
    Deve ser detetado e gerar um aviso sobre wildcard.
    """
    plugin = Plugin()
    # Garante que a flag de aviso está ligada (default é True no teu __init__)
    plugin.warn_wildcard_imports = True
    
    code = "from tkinter import *"
    
    report = plugin.analyze(code, "test.py")
    results = report["results"]
    
    assert len(results) == 1
    message = results[0]["message"]
    
    # Verifica se a mensagem contém o aviso de wildcard
    assert "Importa '*' de 'tkinter'" in message
    assert "wildcard import desencorajado" in message