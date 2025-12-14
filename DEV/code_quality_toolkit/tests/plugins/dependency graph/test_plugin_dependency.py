import json
import time
import unittest

from toolkit.plugins.dependency_graph.plugin import Plugin
from toolkit.utils.config import ToolkitConfig

class UnitTestsDependencyGraph(unittest.TestCase):
    """
    Testes Unitários focados na lógica de parsing (analyze) e no contrato do Plugin.
    Cobre todos os critérios (A-V) - testes originais + testes adicionais de validação.
    """

    def setUp(self):
        """Inicializa o plugin antes de cada teste."""
        self.plugin = Plugin() 
        self.file_path = "my_test_module.py"
        self.config = ToolkitConfig() 
        self.plugin.configure(self.config)
        

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
        # Cria uma config real
        config = ToolkitConfig()
        
        # Altera as regras diretamente no objeto
        config.rules.warn_wildcard_imports = False
        config.rules.max_relative_import_level = 3
        config.rules.track_stdlib_modules = False
        
        # Configura o plugin
        self.plugin.configure(config)
        
        # Verifica se o plugin assumiu os valores
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
        self.assertIn(
            result["summary"]["third_party_count"]
            + result["summary"]["local_count"],
            [1],
        )

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
        """
        Test C: Verifica que todos os imports são capturados, incluindo os
        aninhados, e verifica a linha de código para confirmar a captura.
        """
        
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
        """
        Test E: Verifica se o analyze() falha graciosamente em caso de
        SyntaxError.
        """
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
        
        # Verifica a severidade e a mensagem de aviso
        self.assertEqual(result["results"][0]["severity"], "medium")
        self.assertIn(
            "[AVISO: wildcard import desencorajado]",
            result["results"][0]["message"],
        )

    def test_g_contract_json_structure(self):
        """
        Test G: Verifica se a saída (analyze output) é estruturalmente
        válida JSON.
        """
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

    def test_h_multiple_imports_same_line(self):
        """Test H: Verifica múltiplos imports na mesma linha."""
        code = "import os, sys, json"
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve capturar 3 imports
        self.assertEqual(result["summary"]["total_imports"], 3)
        # Todos da stdlib
        self.assertEqual(result["summary"]["stdlib_count"], 3)

    def test_i_relative_imports_various_levels(self):
        """Test I: Verifica imports relativos de vários níveis."""
        code = """
from . import module1
from .. import module2
from ...package import module3
"""
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(result["summary"]["relative_imports"], 3)
        # Verificar avisos para nível > max_relative_import_level
        high_severity = [r for r in result["results"] if r["severity"] == "medium"]
        self.assertGreater(len(high_severity), 0)

    def test_j_import_with_alias(self):
        """Test J: Verifica imports com alias."""
        code = "import numpy as np\nfrom pandas import DataFrame as DF"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 2)
        # Verificar que hints mencionam os aliases
        hints = [r["hint"] for r in result["results"]]
        self.assertTrue(any("Alias: np" in h for h in hints))
        self.assertTrue(any("Alias: DF" in h for h in hints))

    def test_k_complex_package_structure(self):
        """Test K: Verifica importação de pacotes com estrutura complexa."""
        code = """
from my_project.submodule.utils import helper
from external.lib.version2.api import Client
"""
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 2)
        # Verificar categorização
        summary = result["summary"]
        # Ambos devem ser categorizados como local ou third_party
        self.assertGreater(summary["local_count"] + summary["third_party_count"], 0)

    def test_l_no_track_stdlib(self):
        """Test L: Verifica comportamento quando track_stdlib_modules = False."""
        # Criar nova instância do plugin
        plugin = Plugin()
        
        # Desabilitar tracking de stdlib
        config = ToolkitConfig()
        config.rules.track_stdlib_modules = False
        plugin.configure(config)
        
        code = "import json\nimport my_module"
        result = plugin.analyze(code, self.file_path)
        
        # Não deve incluir json nos resultados
        # (foi filtrado porque é stdlib e track_stdlib_modules = False)
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("my_module", result["results"][0]["message"])

    def test_m_graph_structure_validation(self):
        """Test M: Verifica estrutura completa do grafo de dependências."""
        code = """
from module_a import something
from module_b import other
import module_c
"""
        result = self.plugin.analyze(code, self.file_path)
        
        graph_data = result["summary"]["dependency_graph"]
        
        # Validar estrutura
        self.assertIn("nodes", graph_data)
        self.assertIn("node_count", graph_data)
        self.assertIn("categories", graph_data)
        
        # Validar contagem de nós
        self.assertEqual(graph_data["node_count"], 3)
        self.assertEqual(len(graph_data["nodes"]), 3)
        
        # Validar categorias
        categories = graph_data["categories"]
        self.assertIn("stdlib", categories)
        self.assertIn("third_party", categories)
        self.assertIn("local", categories)

    def test_n_performance_large_file(self):
        """Test N: Verifica performance com ficheiro grande."""
        # Criar código com muitos imports
        imports = [f"import module_{i}" for i in range(100)]
        code = "\n".join(imports)
        
        start_time = time.time()
        result = self.plugin.analyze(code, self.file_path)
        elapsed = time.time() - start_time
        
        # Deve completar em menos de 1 segundo
        self.assertLess(elapsed, 1.0)
        self.assertEqual(result["summary"]["total_imports"], 100)

    def test_o_unicode_module_names(self):
        """Test O: Verifica handling de nomes de módulos com caracteres especiais."""
        # Python 3 permite Unicode em identificadores
        code = "import módulo_português"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("módulo_português", result["results"][0]["message"])

    def test_p_edge_case_empty_module(self):
        """Test P: Verifica edge case de 'from . import something'."""
        code = "from . import helper"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["summary"]["relative_imports"], 1)
        self.assertEqual(result["summary"]["local_count"], 1)

    def test_q_mixed_import_styles(self):
        """Test Q: Verifica mistura de estilos de import."""
        code = """
import os
from sys import argv
import pathlib as pl
from typing import List, Dict, Optional
from . import local_module
from ..parent import helper
"""
        result = self.plugin.analyze(code, self.file_path)
        
        # Contar tipos
        summary = result["summary"]
        self.assertEqual(summary["total_imports"], 6)
        self.assertEqual(summary["relative_imports"], 2)
        self.assertGreater(summary["stdlib_count"], 0)

    def test_r_wildcard_severity_configuration(self):
        """Test R: Verifica configuração de severidade para wildcard imports."""
        # Testar com warn_wildcard_imports = True (padrão)
        code = "from package import *"
        result = self.plugin.analyze(code, self.file_path)
        self.assertEqual(result["results"][0]["severity"], "medium")
        
        # Testar com warn_wildcard_imports = False
        plugin = Plugin()
        config = ToolkitConfig()
        config.rules.warn_wildcard_imports = False
        plugin.configure(config)
        
        result = plugin.analyze(code, self.file_path)
        # Mesmo com aviso desligado, deve ser capturado mas com severidade info
        self.assertEqual(result["results"][0]["severity"], "info")

    def test_s_deep_relative_imports(self):
        """Test S: Verifica avisos para imports relativos profundos."""
        # max_relative_import_level padrão é 1
        code = "from ....deep.package import module"
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve gerar aviso de nível profundo
        self.assertEqual(result["results"][0]["severity"], "medium")
        self.assertIn("[AVISO: nível profundo]", result["results"][0]["message"])

    def test_t_empty_from_module(self):
        """Test T: Verifica from com módulo vazio (import relativo puro)."""
        code = "from . import *"
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve capturar mesmo sem nome de módulo específico
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["summary"]["wildcard_imports"], 1)
        self.assertEqual(result["summary"]["relative_imports"], 1)

    def test_u_status_field_consistency(self):
        """Test U: Verifica consistência do campo status."""
        # Teste com código válido
        code = "import valid_module"
        result = self.plugin.analyze(code, self.file_path)
        self.assertEqual(result["summary"]["status"], "completed")
        
        # Teste com erro de sintaxe
        code_invalid = "import module\nimport"
        result = self.plugin.analyze(code_invalid, self.file_path)
        self.assertEqual(result["summary"]["status"], "failed")

    def test_v_dashboard_integration(self):
        """Test V: Verifica integração com o dashboard plugin."""
        code = """
import os
import sys
from pathlib import Path
from my_project.utils import helper
"""
        result = self.plugin.analyze(code, self.file_path)
        
        # Verificar que os dados podem ser usados pelo dashboard
        self.assertIn("dependency_graph", result["summary"])
        
        graph_data = result["summary"]["dependency_graph"]
        self.assertIsInstance(graph_data["nodes"], list)
        self.assertIsInstance(graph_data["categories"], dict)
        
        # Verificar que as categorias estão corretas
        for category in ["stdlib", "third_party", "local"]:
            self.assertIn(category, graph_data["categories"])
            self.assertIsInstance(graph_data["categories"][category], list)

if __name__ == "__main__":
    # Executar testes com verbosidade
    unittest.main(verbosity=2)