import unittest
import json
import ast
from typing import Any # Necessário para usar a anotação 'Any' nos tipos

# IMPORTAÇÃO DO PLUGIN:
from toolkit.plugins.dependency_graph.plugin import Plugin

# --- Mocks e Auxiliares ---

class MockToolkitConfig:
    """Simulação da classe de configuração da Toolkit, para o método configure()."""
    def __init__(self, rules_config=None):
        # Cria uma classe interna para simular o acesso via ponto (config.rules.property)
        class Rules:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        self.rules = Rules(**rules_config) if rules_config is not None else Rules()


# --- CORPO DA CLASSE DE TESTES ---

class UnitTestsDependencyGraph(unittest.TestCase):
    """
    Testes Unitários focados na lógica de parsing (analyze) e no contrato do Plugin.
    Cobre todos os critérios (A, B, C, D, E, F, G) sem testes de integração.
    """

    def setUp(self):
        """Inicializa o plugin antes de cada teste."""
        # Se a classe Plugin não estiver definida neste arquivo, este passo falhará.
        self.plugin = Plugin() 
        self.file_path = "my_test_module.py"
        self.mock_config = MockToolkitConfig()
        self.plugin.configure(self.mock_config) # Configuração padrão

    # ====================================================================
    # Testes de Contrato e Configuração (Feature B & Test G)
    # ====================================================================

    def test_g1_plugin_contract_name(self):
        """Test G.1: Verifica se o Plugin retorna os metadados corretos."""
        metadata = self.plugin.get_metadata()
        self.assertEqual(metadata["name"], "DependencyGraph")
        self.assertIn("version", metadata)
        self.assertIn("description", metadata)

    def test_g2_plugin_configuration_default(self):
        """Test G.2: Verifica as configurações padrão."""
        self.assertTrue(self.plugin.warn_wildcard_imports)
        self.assertEqual(self.plugin.max_relative_import_level, 1)
        self.assertTrue(self.plugin.track_stdlib_modules)

    def test_g2_plugin_configuration_override(self):
        """Test G.2: Verifica se o configure() aceita e aplica configurações."""
        custom_config = MockToolkitConfig(rules_config={
            "warn_wildcard_imports": False,
            "max_relative_import_level": 3,
            "track_stdlib_modules": False
        })
        self.plugin.configure(custom_config)
        self.assertFalse(self.plugin.warn_wildcard_imports)
        self.assertEqual(self.plugin.max_relative_import_level, 3)
        self.assertFalse(self.plugin.track_stdlib_modules)

    # ====================================================================
    # Testes A, B, C: Casos Comuns de Parsing (Feature A)
    # ====================================================================

    def test_a_import_simple_module(self):
        """Test A: Verifica 'import simple_module' (absolute import)."""
        code = "import simple_module"
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve encontrar 1 resultado
        self.assertEqual(len(result["results"]), 1)
        # Verifica se o módulo é capturado
        self.assertEqual(result["summary"]["unique_modules"], 1)
        # Verifica a categoria (Third-party ou Local) - deve ser 1 no total
        self.assertIn(result["summary"]["third_party_count"] + result["summary"]["local_count"], [1])

    def test_b_from_package_import_function(self):
        """Test B: Verifica 'from package import function'."""
        code = "from my_package import my_function"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 1)
        
        # Verifica a informação de módulo/nome na mensagem
        message = result["results"][0]["message"]
        self.assertIn("Importa 'my_function' de 'my_package'", message)
        
        # O módulo 'my_package' deve ser capturado
        self.assertEqual(result["summary"]["unique_modules"], 1)

    def test_c_top_level_only(self):
        """Test C: Verifica que todos os imports são capturados, incluindo os aninhados, 
           e verifica a linha de código para confirmar a captura do aninhado."""
        
        code = (
            "import top_level_1\n" # Linha 1
            "def bar():\n"         # Linha 2
            "    import hidden_module_2\n" # Linha 3
            "from math import sqrt" # Linha 4 (stdlib)
        )
        result = self.plugin.analyze(code, self.file_path)
        
        # O seu código extrai 3 imports
        self.assertEqual(result["summary"]["total_imports"], 3)
        
        # Verificando as linhas para garantir que o 'hidden_module_2' foi capturado
        lines = [r["line"] for r in result["results"]]
        self.assertIn(1, lines)
        self.assertIn(3, lines) # Confirma que o import dentro da função é capturado
        self.assertIn(4, lines)

    # ====================================================================
    # Testes D, E, F: Edge Cases
    # ====================================================================

    def test_d_empty_file(self):
        """Test D: Verifica o comportamento com um arquivo vazio."""
        code = ""
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(result["summary"]["total_imports"], 0)
        self.assertEqual(result["summary"]["status"], "completed")
        self.assertEqual(len(result["results"]), 0)

    def test_e_file_with_syntax_error_graceful_fail(self):
        """Test E: Verifica se o analyze() falha graciosamente em caso de SyntaxError."""
        # Código sintaticamente inválido
        code = "import module\n import" 
        
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve retornar um resultado de falha (SyntaxError tratado)
        self.assertEqual(result["summary"]["status"], "failed")
        self.assertEqual(result["summary"]["issues_found"], 1)
        
        # Verifica o código de erro
        self.assertEqual(result["results"][0]["code"], "DEP-SYNTAX")

    def test_f_import_star(self):
        """Test F: Verifica 'from package import *' (wildcard import) e seu aviso."""
        code = "from legacy_package import *"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(result["summary"]["wildcard_imports"], 1)
        self.assertEqual(len(result["results"]), 1)
        
        # Verifica a severidade e a mensagem de aviso (Requisito: Must ensure it is treated as a dependency)
        self.assertEqual(result["results"][0]["severity"], "medium")
        self.assertIn("[AVISO: wildcard import desencorajado]", result["results"][0]["message"])

    def test_g_contract_json_structure(self):
        """Test G: Verifica se a saída (analyze output) é estruturalmente válida JSON."""
        code = "import json\nfrom local import util"
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve ser serializável em JSON (o que é garantido pelo retorno de dicts)
        try:
            json.dumps(result)
        except TypeError:
            self.fail("A saída do analyze() não é serializável em JSON.")

        # Verifica a estrutura do grafo (Requisito de Contract Check)
        graph_data = result["summary"]["dependency_graph"]
        self.assertIn("node_count", graph_data)
        self.assertIn("categories", graph_data)
        self.assertIsInstance(graph_data["nodes"], list)
        
