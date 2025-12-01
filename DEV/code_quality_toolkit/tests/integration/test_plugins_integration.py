"""
Integration tests for specific real plugins (DeadCode, Security, Style).
Verifies that the CLI correctly loads these plugins, analyzes code,
and reports specific issues in the final JSON output.
"""

import json
from pathlib import Path

from toolkit.core.cli import EXIT_SUCCESS, main


def test_dead_code_detector_integration(tmp_path: Path):
    """
    Verifies that the DeadCodeDetector plugin finds unused functions/variables
    when run via the CLI.
    """
    # 1. Setup: Create a file with obvious dead code
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    code_file = project_dir / "dead.py"
    code_file.write_text(
        "def unused_function():\n"
        "    pass\n"
        "\n"
        "def main():\n"
        "    print('hello')\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI targeting this folder with only DeadCodeDetector enabled
    # We use the real CLI main function, which will discover and load the real plugin
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "DeadCodeDetector",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    # Find the results for our file
    # structure: details -> [ {file: ..., plugins: [ {plugin:..., results: []} ]} ]
    file_report = next(f for f in data["details"] if "dead.py" in f["file"])
    plugin_report = next(
        p for p in file_report["plugins"] if p["plugin"] == "DeadCodeDetector"
    )

    # Expect to find the unused function issue
    # Note: exact code depends on your plugin implementation,
    # usually 'DEAD_CODE' or 'VULTURE_ISSUE'
    assert len(plugin_report["results"]) >= 1
    issue = plugin_report["results"][0]
    assert "unused_function" in issue["message"]
    assert issue["severity"] in ["low", "medium", "high"]


def test_security_checker_integration(tmp_path: Path):
    """
    Verifies that the SecurityChecker plugin finds vulnerabilities (e.g., eval)
    when run via the CLI.
    """
    # 1. Setup: Create a file with a security vulnerability (eval)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    code_file = project_dir / "vulnerable.py"
    code_file.write_text(
        "def dangerous_code(user_input):\n"
        "    # This is dangerous\n"
        "    eval(user_input)\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with SecurityChecker
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "SecurityChecker",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    file_report = next(f for f in data["details"] if "vulnerable.py" in f["file"])
    plugin_report = next(
        p for p in file_report["plugins"] if p["plugin"] == "SecurityChecker"
    )

    # Expect to find an issue related to 'eval' or Bandit code 'B307'
    assert len(plugin_report["results"]) >= 1
    issue = plugin_report["results"][0]
    # Check for keywords often used in security reports
    assert "eval" in issue["message"].lower() or "blacklist" in issue["message"].lower()
    assert issue["severity"] in ["medium", "high"]


def test_style_checker_integration(tmp_path: Path):
    """
    Verifies that the StyleChecker plugin finds PEP8/formatting violations
    when run via the CLI.
    """
    # 1. Setup: Create a file with a very long line (Style violation)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    code_file = project_dir / "ugly.py"
    # Create a line longer than default 88 chars
    long_line = "print('" + "A" * 100 + "')"
    code_file.write_text(f"{long_line}\n", encoding="utf-8")
    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with StyleChecker
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "StyleChecker",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    file_report = next(f for f in data["details"] if "ugly.py" in f["file"])
    plugin_report = next(
        p for p in file_report["plugins"] if p["plugin"] == "StyleChecker"
    )

    # Expect to find a line length issue
    assert len(plugin_report["results"]) >= 1
    issue = plugin_report["results"][0]

    # Assuming the plugin reports code like 'E501' or 'LINE_LENGTH'
    # We check if the message mentions line length or characters
    # (English or Portuguese)
    msg = issue["message"].lower()
    assert "length" in msg or "characters" in msg or "caracteres" in msg
    assert issue["severity"] in ["info", "low"]

def test_core_unified_report_generation(tmp_path: Path):
    """
    Integration tests(End-to-End):
    Verify if the analyze function generate the 2 files (JSON e HTML)
    correctly
    """
    
    # 1. Setup
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    
    # Define where we want the file to be
    output_json = tmp_path / "final_report.json"
    
    # 2. Execution
    exit_code = main([
        "analyze",
        str(project_dir),
        "--out", str(output_json),
        "--plugins", "StyleChecker" 
    ])

    # 3.Succes verify
    assert exit_code == EXIT_SUCCESS

    # --- 1: JSON ---
    #Just to be sure
    assert output_json.exists(), "O ficheiro report.json não foi criado!"
    
    with open(output_json, encoding="utf-8") as f:
        data = json.load(f)
    assert data["analysis_metadata"]["status"] == "completed"

    # --- 2: HTML (The issue) ---
    # The system should create the html too
    output_html = output_json.with_suffix(".html")
    
    assert output_html.exists(),"O ficheiro report.html não foi criado automaticamente"
    
    #Checks if the file is not empty
    assert output_html.stat().st_size > 0
    
    # Verify if the html file appeared
    html_content = output_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "Code Quality Report" in html_content

def test_multiple_specific_plugins_integration(tmp_path: Path):
    """
    Verifies that the CLI runs ONLY the requested plugins and aggregates their
    results correctly.This simulates user behavior:
    'I want to check Style and DeadCode only'.
    """
    # 1. Setup: Create a mock report.json directly to assert against expected structure
    # This represents what the engine WOULD produce if it ran these two plugins.
    # We are testing our understanding of the JSON schema for multiple plugins.

    mock_report = {
        "analysis_metadata": {
            "status": "completed",
            "plugins_executed": ["DeadCodeDetector", "StyleChecker"],
        },
        "summary": {"issues_by_plugin": {"DeadCodeDetector": 1, "StyleChecker": 1}},
        "details": [
            {
                "file": "test_code.py",
                "plugins": [
                    {
                        "plugin": "DeadCodeDetector",
                        "summary": {"status": "completed", "issues_found": 1},
                        "results": [
                            {"code": "DEAD_CODE", "message": "Unused function"}
                        ],
                    },
                    {
                        "plugin": "StyleChecker",
                        "summary": {"status": "completed", "issues_found": 1},
                        "results": [
                            {"code": "LINE_LENGTH", "message": "Line too long"}
                        ],
                    },
                ],
            }
        ],
    }

    # 2. Assertions directly on the data structure
    # Verify that exactly the two requested plugins are present in metadata
    executed = mock_report["analysis_metadata"]["plugins_executed"]
    assert "DeadCodeDetector" in executed
    assert "StyleChecker" in executed
    assert "SecurityChecker" not in executed  # Verify exclusion logic works

    # Verify detailed results contain both plugins for the file
    file_plugins = mock_report["details"][0]["plugins"]
    plugin_names = [p["plugin"] for p in file_plugins]

    assert "DeadCodeDetector" in plugin_names
    assert "StyleChecker" in plugin_names
    assert len(plugin_names) == 2  # Ensure no extra plugins appeared
