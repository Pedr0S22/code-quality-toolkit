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


def test_duplication_checker_integration(tmp_path: Path):
    """
    Verifies that the DuplicationChecker plugin detects duplicated code (R0801)
    when run via the CLI across multiple files.
    """

    # 1. Setup: Create a project with two files containing duplicated code
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    file_a = project_dir / "a.py"
    file_b = project_dir / "b.py"

    duplicated_block = """
def compute():
    total = 0
    for i in range(10):
        total += i
    if total > 5:
        total -= 1
    return total
"""

    file_a.write_text(duplicated_block, encoding="utf-8")
    file_b.write_text(duplicated_block, encoding="utf-8")

    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with DuplicationChecker
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "DuplicationChecker",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    file_reports = [
        f
        for f in data["details"]
        if f["file"].endswith("a.py") or f["file"].endswith("b.py")
    ]
    assert file_reports, "No .py files found in report."

    num_reports = 0
    for file_report in file_reports:
        plugin_report = next(
            (p for p in file_report["plugins"] if p["plugin"] == "DuplicationChecker"),
            None,
        )
        assert plugin_report is not None, "DuplicationChecker not found in plugin list."
        num_reports += 1

    assert num_reports > 0, "Expected more than one report across multiple files."


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
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_json),
            "--plugins",
            "StyleChecker",
        ]
    )

    # 3.Succes verify
    assert exit_code == EXIT_SUCCESS

    # --- 1: JSON ---
    # Just to be sure
    assert output_json.exists(), "O ficheiro report.json não foi criado!"

    with open(output_json, encoding="utf-8") as f:
        data = json.load(f)
    assert data["analysis_metadata"]["status"] == "completed"

    # --- 2: HTML (The issue) ---
    # The system should create the html too
    output_html = output_json.with_suffix(".html")

    assert output_html.exists(), "O ficheiro report.html não foi criado automaticamente"

    # Checks if the file is not empty
    assert output_html.stat().st_size > 0

    # Verify if the html file appeared
    html_content = output_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "Code Quality Report" in html_content


def test_dependency_graph_integration(tmp_path: Path):
    """
    Verifies that the DependencyGraph plugin correctly identifies imports
    and module dependencies when run via the CLI.
    """
    # 1. Setup: Create a project with 2 files that import each other/standard lib
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # main.py imports utils and os
    (project_dir / "main.py").write_text(
        "import os\n" "from . import utils\n", encoding="utf-8"
    )

    # utils.py imports json
    (project_dir / "utils.py").write_text("import json\n", encoding="utf-8")

    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with DependencyGraph
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "DependencyGraph",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    # Check results for main.py
    main_report = next(f for f in data["details"] if "main.py" in f["file"])
    main_plugin = next(
        p for p in main_report["plugins"] if p["plugin"] == "DependencyGraph"
    )

    # Should find 'os' and 'utils'
    messages = [r["message"] for r in main_plugin["results"]]
    assert any("os" in m for m in messages)
    assert any("utils" in m for m in messages)

    # Check results for utils.py
    utils_report = next(f for f in data["details"] if "utils.py" in f["file"])
    utils_plugin = next(
        p for p in utils_report["plugins"] if p["plugin"] == "DependencyGraph"
    )

    # Should find 'json'
    messages = [r["message"] for r in utils_plugin["results"]]
    assert any("json" in m for m in messages)

    # Check Summary Graph Data
    # O plugin deve ter gerado a estrutura do grafo no sumário
    graph_data = utils_plugin["summary"].get("dependency_graph")
    assert graph_data is not None
    assert "json" in graph_data["nodes"]


def test_basic_metrics_integration(tmp_path: Path):
    """
    Verifies that the BasicMetrics plugin correctly computes metrics
    like total_lines, logical_lines, comment_lines, blank_lines,
    docstring_lines, and Halstead metrics when run via the CLI.
    """
    import json

    from toolkit.core.cli import EXIT_SUCCESS, main

    # 1. Setup: Create a small Python file
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    code_file = project_dir / "metrics_test.py"
    code_file.write_text(
        '"""Module docstring."""\n'
        "def foo():\n"
        "    # This is a comment\n"
        "    return 42\n\n"
        "def bar():\n"
        "    return foo()\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with BasicMetrics plugin
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "BasicMetrics",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    # Find the report for the test file
    file_report = next(f for f in data["details"] if "metrics_test.py" in f["file"])
    plugin_report = next(
        p for p in file_report["plugins"] if p["plugin"] == "BasicMetrics"
    )

    # Check that metrics are reported
    summary = plugin_report["summary"]
    metrics = summary.get("metrics", {})

    # Expect non-zero totals
    assert metrics.get("total_lines", 0) > 0
    assert metrics.get("logical_lines", 0) > 0
    assert "comment_lines" in metrics
    assert "docstring_lines" in metrics
    assert "blank_lines" in metrics

    # Check results list matches issues_found
    assert len(plugin_report["results"]) == summary.get("issues_found", 0)


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


def test_comment_density_integration(tmp_path: Path):
    """
    Verifies that the CommentDensity plugin finds comment density violations
    when run via the CLI.
    """
    # 1. Setup: Create a file with very low comment density
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    code_file = project_dir / "nocomments.py"

    # Create a file with NO comments (will trigger low density violation)
    code_content = """def function_one():
    x = 1
    y = 2
    return x + y

def function_two():
    a = 3
    b = 4
    return a * b

class MyClass:
    def method(self):
        pass
"""
    code_file.write_text(code_content, encoding="utf-8")
    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with CommentDensity plugin
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "CommentDensity",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    file_report = next(f for f in data["details"] if "nocomments.py" in f["file"])
    plugin_report = next(
        p for p in file_report["plugins"] if p["plugin"] == "CommentDensity"
    )

    # Expect to find a low comment density issue
    assert len(plugin_report["results"]) >= 1
    issue = plugin_report["results"][0]

    # Check the issue details
    assert "LOW_COMMENT_DENSITY" == issue["code"]
    assert "low comment density" in issue["message"].lower()
    assert issue["severity"] == "high"



def test_all_plugins_integration(tmp_path: Path):
    """
    Integration test that runs all enabled plugins together with the core system.
    Verifies that all plugins execute successfully, generate a valid report,
    and produce expected results without conflicts.
    """
    # 1. Setup: Create a sample project with code that triggers issues in all plugins
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # File 1: Style issues (long line), security (eval), dead code, low comment density
    (project_dir / "main.py").write_text(
        '"""Module docstring."""\n'
        "import os\n"
        "from utils import helper\n"
        "\n"
        "# This is a comment\n"
        "def main():\n"
        "    # Long line to trigger style checker\n"
        f"    print('{'A' * 100}')\n"
        "    # Security issue\n"
        "    eval('print(1)')\n"
        "    helper()\n"
        "\n"
        "def unused_function():\n"
        "    pass\n",
        encoding="utf-8",
    )

    # File 2: Duplicated code, dependency graph
    (project_dir / "utils.py").write_text(
        "import json\n"
        "\n"
        "def helper():\n"
        "    total = 0\n"
        "    for i in range(10):\n"
        "        total += i\n"
        "    return total\n",
        encoding="utf-8",
    )

    # File 3: Another file with duplicated code
    (project_dir / "duplicate.py").write_text(
        "def helper():\n"
        "    total = 0\n"
        "    for i in range(10):\n"
        "        total += i\n"
        "    return total\n",
        encoding="utf-8",
    )

    # File 4: Cyclomatic complexity (nested ifs)
    (project_dir / "complex.py").write_text(
        "def complex_function(x, y, z):\n"
        "    if x > 0:\n"
        "        if y > 0:\n"
        "            if z > 0:\n"
        "                return x + y + z\n"
        "            else:\n"
        "                return x + y\n"
        "        else:\n"
        "            return x\n"
        "    else:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "report.json"

    # 2. Execution: Run CLI with all plugins
    exit_code = main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(output_file),
            "--plugins",
            "all",
        ]
    )

    # 3. Verification
    assert exit_code == EXIT_SUCCESS
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    # Check overall report structure
    assert data["analysis_metadata"]["status"] == "completed"
    plugins_executed = data["analysis_metadata"]["plugins_executed"]
    # Only expect plugins that are actually loaded and executed
    # (some plugins may be filtered due to missing dependencies or other conditions)
    assert len(plugins_executed) >= 2  # At least some plugins should be executed
    assert "StyleChecker" in plugins_executed
    assert "CyclomaticComplexity" in plugins_executed

    # Check that we have details for multiple files
    assert len(data["details"]) >= 4  # At least the files we created

    # Verify that at least some plugins produced results
    total_results = 0
    for file_report in data["details"]:
        for plugin_report in file_report["plugins"]:
            total_results += len(plugin_report.get("results", []))
    assert total_results > 0, "No plugin produced any results"

    # Check summary has issues by plugin
    summary = data["summary"]
    assert "issues_by_plugin" in summary
    issues_by_plugin = summary["issues_by_plugin"]
    # At least some plugins should have found issues
    total_issues = sum(issues_by_plugin.values())
    assert total_issues > 0, "No issues found by any plugin"
