from textwrap import dedent

from toolkit.plugins.cyclomatic_complexity.plugin import Plugin
from toolkit.utils.config import ToolkitConfig

# ------------------------------
# Helpers para criar configuração
# ------------------------------


def make_config(max_complexity=10, max_length=50, max_args=5):
    """Creates a ToolkitConfig object with rules adjusted."""
    cfg = ToolkitConfig()
    cfg.rules.max_complexity = max_complexity
    cfg.rules.max_function_length = max_length
    cfg.rules.max_arguments = max_args
    return cfg


# ------------------------------
# METADATA TESTS
# ------------------------------


def test_metadata():
    plugin = Plugin()
    m = plugin.get_metadata()

    assert m["name"] == "CyclomaticComplexity"
    assert m["version"] == "0.3.0"
    assert "complexidade" in m["description"].lower()


# ------------------------------
# COMPLEXITY DETECTION
# ------------------------------


def test_high_complexity_violation():
    source = dedent(
        """
        def f(x):
            if x:
                for i in range(5):
                    if i % 2 == 0:
                        try:
                            x += 1
                        except:
                            pass
            return x
    """
    )

    plugin = Plugin()
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
    # 60 linhas dentro da função, todas com indentação correta
    long_body = "\n".join("        x = 1" for _ in range(60))

    source = "def big():\n" f"{long_body}\n" "        return x\n"

    plugin = Plugin()
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
    source = dedent(
        """
        def f(a, b, c, d, e, f, g):
            return 1
    """
    )

    plugin = Plugin()
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
    source = "def broken(:\n   pass"

    plugin = Plugin()

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
    source = dedent(
        """
        def messy(a, b, c, d, e, f):
            if a:
                if b:
                    if c:
                        if d:
                            if e:
                                return 1
            return 0
    """
    )

    plugin = Plugin()
    plugin.configure(make_config(max_complexity=2, max_args=3, max_length=5))

    report = plugin.analyze(source, None)
    codes = [issue["code"] for issue in report["results"]]

    assert "HIGH_COMPLEXITY" in codes
    assert "TOO_MANY_ARGUMENTS" in codes
    assert "LONG_FUNCTION" in codes


# ------------------------------
# NO ISSUES FOUND
# ------------------------------


def test_no_issues_found():
    source = dedent(
        """
        def ok():
            return 123
    """
    )

    plugin = Plugin()
    plugin.configure(make_config(max_complexity=20, max_length=1000, max_args=10))

    report = plugin.analyze(source, None)

    assert report["summary"]["issues_found"] == 0
    assert report["results"] == []
