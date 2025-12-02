"""Testes unitários para o DuplicationChecker Plugin."""

from __future__ import annotations

from unittest.mock import patch

from toolkit.plugins.duplicate_code_checker.plugin import Plugin


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
    """Verifica que um único bloco duplicado é detectado."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    code = "def func():\n    pass\n"
    file_path = tmp_path / "dummy.py"
    file_path.write_text(code)

    mock_stdout = "dummy.py:1:0: R0801: Similar lines in 2 files"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] == 1

    first_issue = report["results"][0]
    assert first_issue["code"] == "R0801"
    assert first_issue["line"] == 1


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
    file_path.write_text(code)

    mock_stdout = (
        "multiple.py:1:0: R0801: Similar lines in 2 files\n"
        "multiple.py:5:0: R0801: Similar lines in 2 files"
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] == 2
    assert len(report["results"]) == 2


def test_duplication_no_issues_found(tmp_path) -> None:
    """Verifica que código único não gera issues."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    code = "unique_line_1\nunique_line_2\nunique_line_3\n"
    file_path = tmp_path / "unique.py"
    file_path.write_text(code)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed("")
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0


def test_duplication_plugin_metadata() -> None:
    """Verifica que o metadata do plugin está correto."""
    plugin = Plugin()
    meta = plugin.get_metadata()

    assert meta["name"] == "DuplicationChecker"
    assert meta["version"] == "0.1.0"
    assert "duplicated" in meta["description"].lower()


def test_duplication_requires_file_path() -> None:
    """Sem file_path o plugin devolve um erro explícito."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    report = plugin.analyze("print('x')", None)

    assert report == {"error": "file_path required"}


def test_duplication_ignores_malformed_pylint_output(tmp_path) -> None:
    """Linhas do pylint mal formatadas com R0801 são ignoradas."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    file_path = tmp_path / "malformed.py"
    file_path.write_text("print('x')\n")

    mock_stdout = "malformed.py:R0801: gibberish sem campos suficientes"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(file_path.read_text(), str(file_path))

    assert report["summary"]["issues_found"] == 0
    assert len(report["results"]) == 0


def test_duplication_summary_severity_high_with_many_issues(tmp_path) -> None:
    """Quando há muitos blocos duplicados, a severidade passa para 'high'."""
    plugin = Plugin()
    plugin.configure(MockToolkitConfig())

    code = (
        "def f1():\n"
        "    x = 1\n"
        "    y = 2\n"
        "\n"
        "def f2():\n"
        "    x = 1\n"
        "    y = 2\n"
        "\n"
        "def f3():\n"
        "    x = 1\n"
        "    y = 2\n"
    )
    file_path = tmp_path / "many_duplicates.py"
    file_path.write_text(code)

    mock_stdout = (
        "many_duplicates.py:1:0: R0801: Similar lines in 2 files\n"
        "many_duplicates.py:5:0: R0801: Similar lines in 2 files\n"
        "many_duplicates.py:9:0: R0801: Similar lines in 2 files"
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _build_mock_completed(mock_stdout)
        report = plugin.analyze(code, str(file_path))

    assert report["summary"]["issues_found"] == 3
    assert len(report["results"]) == 3
