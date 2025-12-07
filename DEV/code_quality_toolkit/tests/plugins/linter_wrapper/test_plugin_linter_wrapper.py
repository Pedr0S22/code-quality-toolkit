"""
Unit tests for the LinterWrapper plugin (Task #156).

Tests cover command construction, output parsing, severity mapping,
and error handling.
"""

import json
from subprocess import TimeoutExpired
from unittest.mock import MagicMock, patch

from toolkit.plugins.linter_wrapper.plugin import Plugin

# --- Mocks de Configuração ---


class MockLinterConfig:
    """Simula a configuração específica do [plugins.linter_wrapper]."""

    def __init__(self):
        self.enabled = True
        self.linters = ["pylint"]
        self.timeout_seconds = 60
        self.max_issues = 500
        self.pylint_args = []
        self.fail_on_severity = "high"


class MockToolkitConfig:
    """Simula o objeto de configuração global."""

    def __init__(self):
        # O plugin acede a config.linter_wrapper
        self.linter_wrapper = MockLinterConfig()


# ==============================================================================
# Test Group A: Command construction & configuration
# ==============================================================================


@patch("subprocess.run")
def test_a_command_construction_with_args(mock_run):
    """
    Test A: Verify specific pylint_args are included in the subprocess command.
    """
    # 1. Arrange
    plugin = Plugin()
    config = MockToolkitConfig()
    config.linter_wrapper.pylint_args = ["--disable=C0111", "--rcfile=myrc"]
    plugin.configure(config)

    # Mock do retorno do subprocess para sucesso (JSON vazio)
    mock_run.return_value = MagicMock(stdout="[]", stderr="", returncode=0)

    # 2. Act
    plugin.analyze("code...", "target_file.py")

    # 3. Assert
    assert mock_run.called
    args, _ = mock_run.call_args
    cmd = args[0]  # O comando é a lista de strings

    # Verificar se o comando base e argumentos extra estão lá
    assert "pylint" in cmd
    assert "--output-format=json" in cmd
    assert "--disable=C0111" in cmd
    assert "--rcfile=myrc" in cmd
    assert "target_file.py" in cmd


@patch("subprocess.run")
def test_b_timeout_configuration(mock_run):
    """Test B: Verify that timeout_seconds is passed to subprocess.run."""
    # 1. Arrange
    plugin = Plugin()
    config = MockToolkitConfig()
    config.linter_wrapper.timeout_seconds = 123
    plugin.configure(config)

    mock_run.return_value = MagicMock(stdout="[]", stderr="", returncode=0)

    # 2. Act
    plugin.analyze("code...", "file.py")

    # 3. Assert
    _, kwargs = mock_run.call_args
    assert kwargs["timeout"] == 123


@patch("subprocess.run")
def test_c_max_issues_truncation(mock_run):
    """Test C: Verify that results are truncated if they exceed max_issues."""
    # 1. Arrange
    plugin = Plugin()
    config = MockToolkitConfig()
    config.linter_wrapper.max_issues = 2
    plugin.configure(config)

    # Simular output do pylint com 3 erros (mais do que o max_issues=2)
    issues = [
        {
            "type": "error",
            "line": 1,
            "column": 0,
            "message": "E1",
            "message-id": "E1",
        },
        {
            "type": "error",
            "line": 2,
            "column": 0,
            "message": "E2",
            "message-id": "E2",
        },
        {
            "type": "error",
            "line": 3,
            "column": 0,
            "message": "E3",
            "message-id": "E3",
        },
    ]
    mock_run.return_value = MagicMock(
        stdout=json.dumps(issues), stderr="", returncode=2
    )

    # 2. Act
    report = plugin.analyze("code...", "file.py")

    # 3. Assert
    assert len(report["results"]) == 2
    # Verificar que truncou corretamente (os dois primeiros)
    assert report["results"][0]["message"] == "E1"
    assert report["results"][1]["message"] == "E2"


# ==============================================================================
# Test Group B: Output parsing & severity mapping
# ==============================================================================


@patch("subprocess.run")
def test_d_output_parsing(mock_run):
    """
    Test D: Verify correct parsing of pylint JSON output.
    """
    plugin = Plugin()
    # Output JSON simulado do Pylint
    pylint_output = [
        {
            "type": "convention",
            "line": 10,
            "column": 4,
            "message": "Missing docstring",
            "message-id": "C0111",
            "symbol": "missing-docstring",
        }
    ]

    mock_run.return_value = MagicMock(
        stdout=json.dumps(pylint_output), stderr="", returncode=16
    )

    report = plugin.analyze("code...", "my_module.py")

    assert len(report["results"]) == 1
    issue = report["results"][0]

    assert issue["line"] == 10
    assert issue["col"] == 4
    assert issue["code"] == "C0111"
    assert issue["message"] == "Missing docstring"
    assert issue["severity"] == "low"  # Convention mapeia para low


@patch("subprocess.run")
def test_e_severity_mapping(mock_run):
    """Test E: Verify mapping of pylint categories to Toolkit severities."""
    plugin = Plugin()

    # Um erro de cada tipo
    pylint_output = [
        {"type": "fatal", "line": 1, "message": "F", "message-id": "F1"},
        {"type": "error", "line": 2, "message": "E", "message-id": "E1"},
        {"type": "warning", "line": 3, "message": "W", "message-id": "W1"},
        {"type": "convention", "line": 4, "message": "C", "message-id": "C1"},
        {"type": "refactor", "line": 5, "message": "R", "message-id": "R1"},
    ]

    mock_run.return_value = MagicMock(
        stdout=json.dumps(pylint_output), stderr="", returncode=0
    )
    report = plugin.analyze("code...", "file.py")
    results = report["results"]

    # Mapeamento esperado
    assert results[0]["severity"] == "high"  # fatal
    assert results[1]["severity"] == "high"  # error
    assert results[2]["severity"] == "medium"  # warning
    assert results[3]["severity"] == "low"  # convention
    assert results[4]["severity"] == "low"  # refactor


# ==============================================================================
# Test Group C: Error handling
# ==============================================================================


@patch("subprocess.run")
def test_g_linter_not_found(mock_run):
    """Test G: Verify FileNotFoundError results in a LINTER_NOT_FOUND issue."""
    plugin = Plugin()
    mock_run.side_effect = FileNotFoundError

    report = plugin.analyze("code...", "file.py")

    assert len(report["results"]) == 1
    issue = report["results"][0]

    assert issue["code"] == "LINTER_NOT_FOUND"
    assert issue["severity"] == "high"


@patch("subprocess.run")
def test_h_timeout_handling(mock_run):
    """Test H: Verify TimeoutExpired results in a LINTER_TIMEOUT issue."""
    plugin = Plugin()
    # TimeoutExpired requer argumentos no construtor
    mock_run.side_effect = TimeoutExpired(cmd="pylint", timeout=60)

    report = plugin.analyze("code...", "file.py")

    assert len(report["results"]) == 1
    issue = report["results"][0]

    assert issue["code"] == "LINTER_TIMEOUT"
    assert issue["severity"] == "high"


@patch("subprocess.run")
def test_i_nonzero_exit_code_success(mock_run):
    """Test I: Verify that non-zero exit code with valid JSON does NOT crash."""
    plugin = Plugin()

    pylint_output = [
        {"type": "error", "message": "An error", "line": 1, "message-id": "E1"}
    ]

    # Exit code 2 (ou outro) é normal no pylint se houver erros
    mock_run.return_value = MagicMock(
        stdout=json.dumps(pylint_output), stderr="", returncode=2
    )

    report = plugin.analyze("code...", "file.py")

    # Deve ter processado o JSON com sucesso
    assert len(report["results"]) == 1
    assert report["results"][0]["message"] == "An error"


@patch("subprocess.run")
def test_j_invalid_json_output(mock_run):
    """Test J: Verify invalid JSON output returns LINTER_OUTPUT_INVALID."""
    plugin = Plugin()

    # Simular output corrompido (não JSON)
    mock_run.return_value = MagicMock(stdout="I am not JSON", stderr="", returncode=0)

    report = plugin.analyze("code...", "file.py")

    assert len(report["results"]) == 1
    issue = report["results"][0]

    assert issue["code"] == "LINTER_OUTPUT_INVALID"
    assert issue["severity"] == "high"


@patch("subprocess.run")
def test_k_crash_no_stdout(mock_run):
    """Test K: Verify non-zero exit code WITHOUT stdout returns LINTER_ERROR."""
    plugin = Plugin()

    # Simular crash do pylint (stderr tem msg, stdout vazio)
    mock_run.return_value = MagicMock(stdout="", stderr="Fatal crash", returncode=1)

    report = plugin.analyze("code...", "file.py")

    assert len(report["results"]) == 1
    issue = report["results"][0]

    assert issue["code"] == "LINTER_ERROR"
    assert "Fatal crash" in issue["hint"]
