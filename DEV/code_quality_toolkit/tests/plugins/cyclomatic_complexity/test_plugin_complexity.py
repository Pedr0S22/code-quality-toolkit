from textwrap import dedent
from types import SimpleNamespace  # Standard library utility for simple objects

# Assuming Plugin and ToolkitConfig are correctly imported
from toolkit.plugins.cyclomatic_complexity.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


# ------------------------------
# Helpers para criar configuração
# ------------------------------


def make_config(max_complexity=10, max_length=50, max_args=5):
    """
    Creates a ToolkitConfig object with a mocked structure for testing.
    """
    cfg = ToolkitConfig()

    # CRITICAL FIX:
    # ToolkitConfig initializes 'plugins' as a restricted 'PluginsConfig' object.
    # We overwrite it entirely with a SimpleNamespace so we can attach
    # arbitrary plugin sections (like 'cyclomatic_complexity') to it.
    cfg.plugins = SimpleNamespace()

    # Create the configuration section for this specific plugin
    plugin_sect = SimpleNamespace(
        max_complexity=max_complexity,
        max_function_length=max_length,
        max_arguments=max_args,
    )

    # Attach the section to our flexible plugins container
    cfg.plugins.cyclomatic_complexity = plugin_sect

    return cfg


# ------------------------------
# METADATA TESTS
# ------------------------------


def test_metadata():
    """Tests the plugin's metadata function."""
    plugin = Plugin()
    m = plugin.get_metadata()

    assert m["name"] == "CyclomaticComplexity"
    assert m["version"] == "0.2.0"
    assert "complexidade" in m["description"].lower()


# ------------------------------
# COMPLEXITY DETECTION
# ------------------------------


def test_high_complexity_violation():
    """Tests detection of functions exceeding max_complexity limit."""
    source = dedent(
        """
        def f(x):
            # Complexity = 1 (base)
            if x:
                # Complexity + 1
                for i in range(5):
                    # Complexity + 1
                    if i % 2 == 0:
                        # Complexity + 1
                        try:
                            # Complexity + 1
                            x += 1
                        except:
                            # Complexity + 1 (Total: 6)
                            pass
            return x
    """
    )

    plugin = Plugin()
    # Configure plugin with a low limit (e.g., 2)
    plugin.configure(make_config(max_complexity=2))

    report = plugin.analyze(source, "sample.py")

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]

    assert issue["code"] == "HIGH_COMPLEXITY"
    assert issue["severity"] in ("medium", "high")
    assert "complexidade" in issue["message"].lower()


# ------------------------------
# LONG FUNCTION DETECTION
# ------------------------------


def test_long_function_detection():
    """Tests detection of functions exceeding max_function_length limit."""
    # 60 lines inside the function body
    long_body = "\n".join("        x = 1" for _ in range(60))

    source = "def big():\n" f"{long_body}\n" "        return x\n"

    plugin = Plugin()
    # Configure plugin with a low line limit (e.g., 20)
    plugin.configure(make_config(max_length=20))

    report = plugin.analyze(source, "test.py")

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]

    assert issue["code"] == "LONG_FUNCTION"
    assert issue["severity"] in ("low", "medium")


# ------------------------------
# TOO MANY ARGUMENTS
# ------------------------------


def test_too_many_arguments():
    """Tests detection of functions exceeding max_arguments limit."""
    source = dedent(
        """
        def f(a, b, c, d, e, f, g): # 7 arguments
            return 1
    """
    )

    plugin = Plugin()
    # Configure plugin with a low argument limit (e.g., 3)
    plugin.configure(make_config(max_args=3))

    report = plugin.analyze(source, None)

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]

    assert issue["code"] == "TOO_MANY_ARGUMENTS"
    assert "arguments" in issue["message"].lower()


# ------------------------------
# SYNTAX ERROR HANDLING
# ------------------------------


def test_syntax_error_handling():
    """Tests plugin resilience to syntax errors in the source code."""
    source = "def broken(:\n    pass"

    plugin = Plugin()
    # No configuration needed, defaults should apply

    report = plugin.analyze(source, None)

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]

    assert issue["code"] == "SYNTAX_ERROR"
    assert issue["severity"] == "high"
    assert "sintaxe" in issue["message"].lower()


# ------------------------------
# MULTIPLE ISSUES IN SAME FUNCTION
# ------------------------------


def test_multiple_issues_detected():
    """Tests detection of multiple violations in a single function."""
    source = dedent(
        """
        def messy(a, b, c, d, e, f): # 6 args
            # Function is 9 lines long
            if a: # Complexity +1
                if b: # Complexity +1
                    if c: # Complexity +1
                        if d: # Complexity +1
                            if e: # Complexity +1 (Total Complexity: 6)
                                return 1
            return 0
    """
    )

    plugin = Plugin()
    # Set all limits very low to guarantee three violations:
    # Complexity > 2, Args > 3, Length > 5
    plugin.configure(make_config(max_complexity=2, max_args=3, max_length=5))

    report = plugin.analyze(source, None)
    codes = [issue["code"] for issue in report["results"]]

    assert len(codes) == 3
    assert "HIGH_COMPLEXITY" in codes
    assert "TOO_MANY_ARGUMENTS" in codes
    assert "LONG_FUNCTION" in codes


# ------------------------------
# NO ISSUES FOUND
# ------------------------------


def test_no_issues_found():
    """Tests a case where a simple function finds no issues."""
    source = dedent(
        """
        def ok():
            return 123
    """
    )

    plugin = Plugin()
    # Configure with very generous limits
    plugin.configure(make_config(max_complexity=20, max_length=1000, max_args=10))

    report = plugin.analyze(source, None)

    assert report["summary"]["issues_found"] == 0
    assert report["results"] == []