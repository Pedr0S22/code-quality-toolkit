import ast
from textwrap import dedent

# I001: Bloco de importações locais/do projeto
from toolkit.plugins.dead_code_detector.plugin import Plugin, _DefUseVisitor
from toolkit.utils.config import ToolkitConfig

# ======================================================================
# Classes Mock para Simular a Configuração
# ======================================================================


class MockSection:
    """Simula a secção [plugins.dead_code]."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockToolkitConfig:
    """Simula o objeto ToolkitConfig com a secção plugins."""

    def __init__(self, dead_code_config):
        # Cria um objeto que simula config.plugins.dead_code
        self.plugins = type("Plugins", (object,), {"dead_code": dead_code_config})()


# ======================================================================
# 1. Testes do Visitor (Lógica Central)
# ======================================================================


def test_defuse_visitor_basic_logic() -> None:
    """Verifica se o visitor coleta definições e usos básicos corretamente."""
    src = dedent(
        """
        def used_func(): pass
        def unused_func(): pass 
        
        VAR_A = 10 
        VAR_B = 20 
        
        result = used_func() 
        print(VAR_A) 
        """
    )
    tree = ast.parse(src)
    visitor = _DefUseVisitor()
    visitor.visit(tree)

    dead_candidates = set(visitor.defs.keys()) - visitor.uses
    assert "unused_func" in dead_candidates
    assert "VAR_B" in dead_candidates


def test_defuse_visitor_imports() -> None:
    """Verifica se o visitor identifica nomes importados."""
    src = dedent(
        """
        import os
        from sys import path
        from time import time as t
        
        def local_func(): pass
        
        os.getenv('HOME')
        path.append('/tmp')
        t()
        """
    )
    tree = ast.parse(src)
    visitor = _DefUseVisitor()
    visitor.visit(tree)

    assert visitor.imports == {"os", "path", "t"}
    assert "local_func" in visitor.defs

    # ======================================================================


# 2. Testes de Metadados e Configuração
# ======================================================================


def test_plugin_metadata() -> None:
    """Verifica se get_metadata() retorna as informações corretas."""
    plugin = Plugin()
    metadata = plugin.get_metadata()
    assert metadata["name"] == "DeadCodeDetector"
    assert metadata["version"] == "0.1.0"


def test_plugin_configuration_defaults() -> None:
    """Verifica os valores por omissão."""
    plugin = Plugin()
    assert len(plugin.ignore_patterns) == 1
    assert plugin.ignore_patterns[0].pattern == r"^__"


def test_plugin_configuration_custom_settings() -> None:
    """Verifica se a configuração personalizada é aplicada corretamente."""
    dead_code_config = MockSection(
        ignore_patterns=["^test_", "TEMP$"],
        severity="medium",
        min_name_length=5,
    )
    config = MockToolkitConfig(dead_code_config)

    plugin = Plugin()
    plugin.configure(config)

    assert len(plugin.ignore_patterns) == 2
    assert plugin.ignore_patterns[0].pattern == r"^test_"
    assert plugin.min_name_len == 5


def test_plugin_ignored_helper() -> None:
    """Testa a função interna _ignored, verificando min_name_len e patterns."""
    dead_code_config = MockSection(
        ignore_patterns=["^test_"],
        min_name_length=5,
    )
    config = MockToolkitConfig(dead_code_config)

    plugin = Plugin()
    plugin.configure(config)

    assert plugin.min_name_len == 5
    assert plugin._ignored("a") is True
    assert plugin._ignored("abcde") is False


def test_plugin_configuration_no_section() -> None:
    """Verifica que a ausência de secção de plugin não causa erro."""

    class MockNoPluginsConfig:
        plugins = None

    plugin = Plugin()
    plugin.configure(MockNoPluginsConfig())
    assert plugin.severity == "low"

    # ======================================================================


# 3. Testes da Lógica de Análise (analyze) e Resultados
# ======================================================================


def test_analyze_dead_code_basic() -> None:
    """Caso básico: deteta função e variável não utilizadas."""
    src = dedent(
        """
        def used(): return 1
        def unused(): return 2 
        x = used() 
        """
    )
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    out = plugin.analyze(src, "sample.py")

    assert out["summary"]["status"] == "completed"
    assert out["summary"]["issues_found"] == 2

    codes = {issue["code"] for issue in out["results"]}
    assert "DEAD_CODE" in codes


def test_analyze_syntax_error_returns_partial() -> None:
    """Verifica que erros de sintaxe devolvem status 'partial'."""
    plugin = Plugin()
    out = plugin.analyze("def x(:\n pass", "bad.py")

    assert out["summary"]["status"] == "partial"
    assert out["summary"]["issues_found"] == 1
    assert out["results"][0]["code"] == "SYNTAX_ERROR"


def test_analyze_dead_code_in_class_variable_and_function() -> None:
    """Testa código morto em variáveis e métodos de classe."""
    src = dedent(
        """
        UNUSED_GLOBAL = 1 
        
        class MyClass: 
            UNUSED_VAR = 10 
            
            def used_method(self):
                return 1

            def unused_method(self): 
                return 2

        instance = MyClass() 
        instance.used_method() 
        """
    )
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    out = plugin.analyze(src, "class_test.py")

    # O plugin reporta 4 problemas (UNUSED_GLOBAL, MyClass, used_method, unused_method).
    assert out["summary"]["issues_found"] == 4

    dead_names = {issue["message"].split("'")[1] for issue in out["results"]}
    assert "UNUSED_GLOBAL" in dead_names
    assert "unused_method" in dead_names


def test_analyze_ignore_patterns() -> None:
    """Verifica se nomes ignorados pela configuração não são reportados."""
    src = dedent(
        """
        def __private_func(): pass 
        def test_helper(): pass 
        x = 5 
        def regular_dead_func(): pass 
        """
    )
    dead_code_config = MockSection(
        ignore_patterns=["^test_", "^__"],
        min_name_length=1,
    )
    config = MockToolkitConfig(dead_code_config)

    plugin = Plugin()
    plugin.configure(config)

    out = plugin.analyze(src, "ignore_test.py")

    assert out["summary"]["status"] == "completed"
    assert out["summary"]["issues_found"] == 2

    dead_names = {issue["message"].split("'")[1] for issue in out["results"]}
    assert "regular_dead_func" in dead_names
    assert "x" in dead_names


def test_analyze_no_false_positive_on_used_name() -> None:
    """Garante que código usado não é sinalizado."""
    src = dedent(
        """
        def called_func(): 
            return 1
        
        CONSTANT_VALUE = called_func()

        x = CONSTANT_VALUE
        print(x)
        """
    )
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    out = plugin.analyze(src, "safe_code.py")

    assert out["summary"]["status"] == "completed"
    assert out["summary"]["issues_found"] == 0
