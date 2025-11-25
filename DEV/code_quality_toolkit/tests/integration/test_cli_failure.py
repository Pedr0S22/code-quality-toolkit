"""
Integration tests for CLI failure modes.
Verifies that the CLI handles plugin errors gracefully from a user perspective.
"""

import json
from pathlib import Path
from unittest.mock import patch

from toolkit.core.cli import EXIT_MANAGED_ERROR, EXIT_SEVERITY_ERROR, EXIT_SUCCESS, main
from toolkit.core.errors import PluginLoadError

# --- Mock Plugin ---


class Plugin:
    """A plugin that crashes when analyze() is called."""

    def get_metadata(self):
        return {
            "name": "CrashingPlugin",
            "version": "0.0.1",
            "description": "Always crashes",
        }

    def analyze(self, source_code: str, file_path: str | None):
        # Simulate an unexpected runtime error
        raise RuntimeError("Something went terribly wrong inside the plugin!")


# --- Tests ---


def test_cli_exit_code_on_plugin_load_failure(tmp_path: Path, capsys):
    """
    Requirement: CLI must exit with a specific error code (1)
    when a plugin fails to load.
    """
    # Create a dummy project to analyze
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')", encoding="utf-8")

    # Mock load_plugins to simulate a failure
    # (e.g., missing dependency or syntax error in plugin)
    with patch(
        "toolkit.core.cli.load_plugins",
        side_effect=PluginLoadError("Could not load plugin 'BadPlugin'"),
    ):

        # Execute CLI command: toolkit analyze <path>
        exit_code = main(["analyze", str(project_dir)])

    # Verify exit code is 1 (EXIT_MANAGED_ERROR)
    assert exit_code == EXIT_MANAGED_ERROR

    # Verify the error message was printed to stderr
    captured = capsys.readouterr()
    assert "Could not load plugin 'BadPlugin'" in captured.err


def test_cli_partial_report_on_plugin_runtime_failure(tmp_path: Path):
    """
    Requirement:
    1. CLI must NOT crash (python traceback) when a plugin fails
        during execution.
    2. report.json must be generated.
    3. The status in report.json must be 'partial'.
    """
    # Setup dummy project
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('code')", encoding="utf-8")
    output_file = tmp_path / "report.json"

    # Mock load_plugins to return our CrashingPlugin
    # We also mock 'config' to ensure defaults are used
    with patch(
        "toolkit.core.cli.load_plugins", return_value={"CrashingPlugin": Plugin()}
    ):

        # Run analysis
        # Note: Without --fail-on-severity, the CLI should exit 0 (Success)
        # because the engine handled the error gracefully.
        exit_code = main(["analyze", str(project_dir), "--out", str(output_file)])

    # 1. Verify it finished gracefully (Code 0)
    assert exit_code == EXIT_SUCCESS

    # 2. Verify report.json exists
    assert output_file.exists()

    # 3. Verify content of report.json
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    # Check global status
    assert data["analysis_metadata"]["status"] == "partial"

    # Check that the plugin error was recorded in the details
    # The engine should have caught the RuntimeError and logged it as
    # a High Severity issue
    file_details = data["details"][0]
    plugin_results = file_details["plugins"][0]

    assert plugin_results["plugin"] == "CrashingPlugin"
    # The engine wrapper catches the error and sets status to failed
    assert plugin_results["summary"]["status"] == "failed"

    # Ensure the synthetic error was added to results
    assert len(plugin_results["results"]) > 0
    error_entry = plugin_results["results"][0]
    assert error_entry["code"] == "PLUGIN_ERROR"
    assert "Something went terribly wrong" in error_entry["message"]


def test_cli_exit_code_on_severity_failure(tmp_path: Path):
    """
    Requirement: CLI must exit with non-zero code if --fail-on-severity is triggered
    by the crashing plugin (which produces a HIGH severity error).
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('code')", encoding="utf-8")

    # The CrashingPlugin generates a HIGH severity error.
    # If we run with --fail-on-severity high, the CLI
    # should return EXIT_SEVERITY_ERROR (3).
    with patch(
        "toolkit.core.cli.load_plugins", return_value={"CrashingPlugin": Plugin()}
    ):

        exit_code = main(["analyze", str(project_dir), "--fail-on-severity", "high"])

    # Verify exit code is 3 (EXIT_SEVERITY_ERROR)
    assert exit_code == EXIT_SEVERITY_ERROR
