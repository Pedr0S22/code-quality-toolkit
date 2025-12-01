"""Testes Unitários para o DuplicationChecker Plugin."""
from unittest.mock import patch

from toolkit.plugins.duplicate_code_checker.plugin import Plugin


class MockRulesConfig:
    """Mock simples para compatibilidade."""
    max_line_length = 88


class MockToolkitConfig:
    """Mock do ToolkitConfig que usa o MockRulesConfig."""
    def __init__(self):
        self.rules = MockRulesConfig()


def test_duplication_detects_simple_repeat(tmp_path):
    plugin = Plugin()
    config = MockToolkitConfig()
    plugin.configure(config)

    code = "def func():\n    pass\n"
    file_path = tmp_path / "dummy.py"
    file_path.write_text(code)

    mock_stdout = "dummy.py:1:0: R0801: Similar lines in 2 files"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = mock_stdout
        mock_run.return_value.returncode = 0
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] >= 1, "expected at least one issue"


def test_duplication_detects_multiple_repeats(tmp_path):
    """Verifica que múltiplos blocos duplicados são detectados."""

    plugin = Plugin()
    config = MockToolkitConfig()
    plugin.configure(config)

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
    file_path.write_text(code)

    # Mock Pylint output to simulate two duplicates
    mock_stdout = (
        "multiple.py:1:0: R0801: Similar lines in 2 files\n"
        "multiple.py:5:0: R0801: Similar lines in 2 files"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = mock_stdout
        mock_run.return_value.returncode = 0

        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] >= 2, "Expected at least 2 issues"

    summary_entry = report["results"][-1]
    assert summary_entry["entity"] == "bloco duplicado"
    assert len(summary_entry["line_numbers"]) >= 2


def test_duplication_no_issues_found(tmp_path):
    """Verifica que código único não gera issues."""

    plugin = Plugin()
    config = MockToolkitConfig()
    plugin.configure(config)

    code = "unique_line_1\nunique_line_2\nunique_line_3\n"
    file_path = tmp_path / "unique.py"
    file_path.write_text(code)

    report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 1  # Apenas o summary entry


def test_duplication_plugin_metadata():
    """Verifica que o metadata do plugin está correto."""

    plugin = Plugin()
    meta = plugin.get_metadata()

    assert meta["name"] == "DuplicationChecker"
    assert meta["version"] == "0.1.0"
    assert "duplicated" in meta["description"].lower()
