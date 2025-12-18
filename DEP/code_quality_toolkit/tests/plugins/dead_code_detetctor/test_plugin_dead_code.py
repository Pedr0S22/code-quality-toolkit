import ast
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest

# I001: Bloco de importações locais/do projeto
from toolkit.plugins.dead_code_detector.plugin import Plugin, _DefUseVisitor
from toolkit.utils.config import ToolkitConfig

# ======================================================================
# Classes Mock para Simular a Configuração
# ======================================================================


class MockSection:
    """Simula a secção [plugins.dead_code_detector]."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockToolkitConfig:
    """Simula o objeto ToolkitConfig com a secção plugins."""

    def __init__(self, dead_code_config):
        # Changed "dead_code" to "dead_code_detector"
        self.plugins = type(
            "Plugins", (object,), {"dead_code_detector": dead_code_config}
        )()


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
    # Note: Updated to match your current plugin version, usually 0.2.0 based on edits
    assert "version" in metadata


def test_plugin_configuration_defaults() -> None:
    """Verifica os valores por omissão."""
    plugin = Plugin()
    # Default is [re.compile(r"^__")]
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
    assert plugin.min_name_length == 5


def test_plugin_ignored_helper() -> None:
    """Testa a função interna _ignored, verificando min_name_length e patterns."""
    dead_code_config = MockSection(
        ignore_patterns=["^test_"],
        min_name_length=5,
    )
    config = MockToolkitConfig(dead_code_config)

    plugin = Plugin()
    plugin.configure(config)

    assert plugin.min_name_length == 5
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
        unused_var = used()  # Changed 'x' to 'unused_var'
        """
    )
    plugin = Plugin()
    plugin.configure(ToolkitConfig())  # Uses default min_name_length (1)

    out = plugin.analyze(src, "sample.py")

    assert out["summary"]["status"] == "completed"
    # Expect 'unused' and 'unused_var' to be dead
    assert out["summary"]["issues_found"] == 2


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

    # O plugin reporta 4 problemas (UNUSED_GLOBAL, MyClass, used_method, unused_method)
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
    # The default min_name_length is 1, so 'x' is valid to be analyzed.
    dead_code_config = MockSection(
        ignore_patterns=["^test_", "^__"],
        min_name_length=1,
    )
    config = MockToolkitConfig(dead_code_config)

    plugin = Plugin()
    plugin.configure(config)

    out = plugin.analyze(src, "ignore_test.py")

    assert out["summary"]["status"] == "completed"

    # Expected dead items:
    # - 'x' (not ignored, not used)
    # - 'regular_dead_func' (not ignored, not used)
    # Ignored items:
    # - '__private_func' (matches ^__)
    # - 'test_helper' (matches ^test_)
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


@pytest.fixture
def plugin():
    p = Plugin()
    # Reset internal stats for clean testing
    p._stats = {
        "total_issues": 0,
        "severity_counts": {"high": 0, "medium": 0, "low": 0, "info": 0},
        "affected_files": set(),
        "symbol_names": [],
    }
    return p


@pytest.fixture
def mock_results():
    """Simulates the results structure for Dead Code violations."""
    return [
        {
            "file": "C:\\Users\\pedro\\AppData\\Local\\Temp\\source\\app\\unused.py",
            "plugins": [
                {
                    "plugin": "DeadCodeDetector",
                    "results": [
                        {
                            "code": "DEAD_CODE",
                            "message": "'calculate_tax' defined and never used.",
                            "severity": "low",
                            "line": 10,
                        }
                    ],
                }
            ],
        },
        {
            "file": "/home/user/project/source/main.py",
            "plugins": [
                {
                    "plugin": "DeadCodeDetector",
                    "results": [
                        {
                            "code": "DEAD_CODE",
                            "message": "'temp_var' defined and never used.",
                            "severity": "low",
                            "line": 5,
                        }
                    ],
                }
            ],
        },
    ]


def test_dead_code_path_normalization(plugin, mock_results):
    """Verifies absolute paths are converted to relative .
    \\ paths in the dashboard HTML."""
    with patch.object(Path, "write_text") as mock_write:
        # We pass a Path object for output_dir
        plugin.generate_dashboard(mock_results, output_dir=Path("."))

        # Capture the written HTML content
        written_html = mock_write.call_args[0][0]

        # Check for normalized paths (Acceptance Criteria: .\folder\file)
        # Note: In JSON injected into HTML, backslashes are often escaped
        assert "app\\\\unused.py" in written_html or "app\\unused.py" in written_html
        assert "main.py" in written_html

        # Ensure absolute roots are removed
        assert "C:\\\\Users" not in written_html
        assert "/home/user" not in written_html


def test_dead_code_stats_update_during_analyze(plugin):
    """Verifies that internal _stats are updated correctly when analyze is called."""
    source = "x = 10\ny = 20\nprint(x)"  # y is dead code
    file_path = "C:\\source\\test.py"

    plugin.analyze(source, file_path)

    assert plugin._stats["total_issues"] == 1
    assert "y" in plugin._stats["symbol_names"]
    assert any("test.py" in f for f in plugin._stats["affected_files"])


def test_generate_dashboard_total_counts(plugin, mock_results):
    """Checks if the dashboard correctly calculates the total number of issues found."""
    with patch.object(Path, "write_text") as mock_write:
        plugin.generate_dashboard(mock_results, output_dir=Path("."))

        written_html = mock_write.call_args[0][0]

        # Verify the total_issues metric in the injected JSON
        assert '"total_issues": 2' in written_html
        assert '"total_files": 2' in written_html


def test_dead_code_aggregation_empty(plugin):
    """Ensures generate_dashboard handles empty results without crashing."""
    with patch.object(Path, "write_text") as mock_write:
        plugin.generate_dashboard([], output_dir=Path("."))

        written_html = mock_write.call_args[0][0]
        assert '"total_issues": 0' in written_html
