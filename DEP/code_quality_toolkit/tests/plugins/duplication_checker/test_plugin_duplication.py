"""Testes unitários para o DuplicationChecker Plugin."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# --- FIX: Mock Jinja2 before importing the plugin ---
# We mock this BEFORE the import because the Plugin module initializes
# jinja2.PackageLoader immediately upon import.

# 1. Create the mocks
mock_jinja = MagicMock()
mock_loader = MagicMock()
mock_env_instance = MagicMock()
mock_template = MagicMock()

# 2. Configure the mocks to behave like real Jinja2
# This is CRITICAL: We must ensure render() returns a STRING, not a Mock.
# Otherwise, integration tests that use this cached module will crash
# with "write() argument must be str, not MagicMock".
mock_template.render.return_value = "<html>Mocked Report</html>"
mock_env_instance.get_template.return_value = mock_template

# 3. Wire them up to the module structure
mock_jinja.Environment.return_value = mock_env_instance
mock_jinja.PackageLoader = MagicMock(return_value=mock_loader)
mock_jinja.select_autoescape = MagicMock()

# 4. Apply the patch to sys.modules
sys.modules["jinja2"] = mock_jinja
# ----------------------------------------------------

# noqa: E402 tells the linter to ignore the "import not at top" error for this line
from toolkit.plugins.duplication_checker.plugin import Plugin  # noqa: E402


class MockRulesConfig:
    """Mock simples para compatibilidade com ToolkitConfig."""

    max_line_length = 88


class MockToolkitConfig:
    """Mock de ToolkitConfig, apenas com a secção 'rules'."""

    def __init__(self) -> None:
        self.rules = MockRulesConfig()


def _build_mock_completed(stdout: str):
    """Helper para simular subprocess.run(...)."""

    class DummyCompleted:
        def __init__(self, out: str) -> None:
            self.stdout = out
            self.returncode = 0

    return DummyCompleted(stdout)


def test_duplication_detects_simple_repeat(tmp_path) -> None:
    """Verifies that a simple duplicated block is detected."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    # Create a file with a repeated 2-line block
    code = "def func():\n" "    pass\n" "def func():\n" "    pass\n"
    file_path = tmp_path / "dummy.py"
    file_path.write_text(code, encoding="utf-8")

    # Run analyze (no subprocess mocking)
    report = plugin.analyze(code, str(file_path))

    # Basic assertions
    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 1
    assert len(report["results"]) == 1

    issue = report["results"][0]
    assert issue["code"] == "DUP_SIMPLE"
    assert "Duplicate code detected" in issue["message"]


def test_duplication_detects_multiple_repeats(tmp_path) -> None:
    """Verifica que múltiplos blocos duplicados são detectados."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    code = (
        "def func1():\n"
        "    x = 1\n"
        "    y = 2\n"
        "\n"
        "def func2():\n"
        "    x = 1\n"
        "    y = 2\n"
        "\n"
        "def func3():\n"
        "    x = 1\n"
        "    y = 2\n"
    )
    file_path = tmp_path / "multiple.py"
    file_path.write_text(code, encoding="utf-8")

    mock_stdout = (
        "multiple.py:1:0: R0801: Similar lines in 2 files\n"
        "multiple.py:5:0: R0801: Similar lines in 2 files"
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 3
    assert len(report["results"]) == 3


def test_duplication_no_issues_found(tmp_path) -> None:
    """Verifica que código único não gera issues."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    code = "unique_line_1\nunique_line_2\nunique_line_3\n"
    file_path = tmp_path / "unique.py"
    file_path.write_text(code, encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed("")
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0


def test_duplication_plugin_metadata() -> None:
    """Verifica que o metadata do plugin está correto."""
    plugin = Plugin()
    meta = plugin.get_metadata()

    assert meta["name"] == "DuplicationChecker"
    assert meta["version"] == "0.1.0"


def test_duplication_requires_file_path() -> None:
    """Sem file_path o plugin devolve um erro explícito."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    report = plugin.analyze("print('x')", None)

    assert report == {"error": "file_path required"}


def test_duplication_ignores_malformed_pylint_output(tmp_path) -> None:
    """Linhas do pylint mal formatadas são ignoradas."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    file_path = tmp_path / "malformed.py"
    file_path.write_text("print('x')\n", encoding="utf-8")

    mock_stdout = "malformed.py:R0801: gibberish sem campos suficientes"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(file_path.read_text(encoding="utf-8"), str(file_path))

    assert report["summary"]["issues_found"] == 0


def test_duplication_render_html() -> None:
    """Testa a renderização do HTML (com template mockado)."""
    plugin = Plugin()
    results = {
        "results": [],
        "summary": {"issues_found": 0, "status": "completed"},
    }
    html = plugin.render_html(results)
    assert len(html) > 0


@pytest.fixture
def plugin():
    return Plugin()


@pytest.fixture
def mock_results():
    """Simulates the results structure for Duplication violations."""
    return [
        {
            "file": "C:\\Users\\pedro\\AppData\\Local\\Temp\\source\\app\\main.py",
            "plugin": "DuplicationChecker",
            "code": "DUP_SIMPLE",
            "line": 10,
            "message": "Duplicate code detected",
        },
        {
            "file": "/home/user/project/source/utils/helper.py",
            "plugin": "DuplicationChecker",
            "code": "DUP_SIMPLE",
            "line": 50,
            "message": "Duplicate code detected",
        },
    ]


def test_duplication_aggregation_logic(plugin, mock_results):
    """Tests if metrics and file counts are aggregated correctly for the UI."""
    aggregated = plugin._aggregate_data_for_dashboard(mock_results)

    # Check general metrics
    assert aggregated["metrics"]["total_files"] == 2
    assert aggregated["metrics"]["total_issues"] == 2

    # Check rule counts
    assert aggregated["rule_counts"][0]["code"] == "DUPLICATED_CODE"
    assert aggregated["rule_counts"][0]["count"] == 2

    # Verify Top Files list contains the paths
    top_files = [f["file"] for f in aggregated["top_files"]]
    assert any("main.py" in f for f in top_files)
    assert any("helper.py" in f for f in top_files)


def test_aggregation_with_dictionary_input(plugin):
    """Ensures the aggregator can handle results wrapped in a 'results' dictionary."""
    wrapped_results = {"results": [{"file": "source/test.py", "code": "DUP_SIMPLE"}]}
    aggregated = plugin._aggregate_data_for_dashboard(wrapped_results)
    assert aggregated["metrics"]["total_issues"] == 1
    assert aggregated["metrics"]["total_files"] == 1
