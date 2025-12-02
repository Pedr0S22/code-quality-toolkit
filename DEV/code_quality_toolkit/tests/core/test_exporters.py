import html
from toolkit.core.exporters import generate_html
from unittest.mock import MagicMock

# --- Mock Data Structure (Complete) ---
def get_mock_unified_report():
    """Returns a comprehensive mock UnifiedReport dictionary."""
    return {
        "analysis_metadata": {
            "timestamp": "2025-12-02 17:30:00",
            "tool_version": "0.1.0",
            "status": "COMPLETED",
            "plugins_executed": ["P1", "P2"],
        },
        "summary": {
            "total_files": 2,
            "total_issues": 5,
            "issues_by_severity": {"high": 2, "medium": 3, "low": 0, "info": 0},
            "issues_by_plugin": {"P1": 2, "P2": 3},
            "top_offenders": [
                {"file": "file_A.py", "issues": 3},
                {"file": "file_B.py", "issues": 2},
            ],
        },
        "details": [
            {
                "file": "file_A.py",
                "plugins": [
                    {
                        "plugin": "P1",
                        "summary": {"issues_found": 2, "status": "completed"},
                        "results": [
                            {
                                "severity": "high",
                                "code": "C101",
                                "message": "Example High Issue",
                                "line": 5,
                                "col": 10,
                                "hint": "Check the documentation for C101.",
                            },
                            {
                                "severity": "medium",
                                "code": "C201",
                                "message": "Example Medium Issue",
                                "line": 15,
                                "col": 1,
                            },
                        ],
                    }
                ],
            },
            {
                "file": "file_B.py",
                "plugins": [
                    {
                        "plugin": "P2",
                        "summary": {
                            "issues_found": 3,
                            "status": "failed",
                            "metrics": {"loc": 50, "coverage": 0.8}, # Has metrics
                            "error": "Timeout during analysis.", # Has error
                        },
                        "results": [
                            # Issue with empty hint/no hint is okay for coverage
                            {"severity": "high", "code": "B1", "message": "Msg B1", "line": 1},
                            {"severity": "medium", "code": "B2", "message": "Msg B2", "line": 2},
                            {"severity": "medium", "code": "B3", "message": "Msg B3", "line": 3},
                        ],
                    }
                ],
            },
        ],
    }


def test_generate_html_with_complete_report():
    """Testa a geração de HTML com um relatório completo (cobertura base)."""
    report = get_mock_unified_report()
    html_output = generate_html(report)

    # Basic structure checks
    assert "Code Quality Toolkit Report" in html_output
    assert "Analysis Metadata" in html_output
    
    # FIX 1: Corrected assertion to match exact output structure (no newline/tab in output)
    assert "<li><strong>Total Issues:</strong> 5</li>" in html_output
    
    assert "high: 2" in html_output
    assert "Plugin: P1" in html_output
    assert "File: file_A.py" in html_output
    assert "Example High Issue" in html_output

    # Check the hint is correctly included
    assert "(Line 5, Col 10)" in html_output
    assert "<em>Hint: Check the documentation for C101.</em>" in html_output

    # Check metrics and error (Lines 144-150 coverage)
    assert "<li>Metrics: loc=50, coverage=0.8</li>" in html_output
    assert "<li>Error: Timeout during analysis.</li>" in html_output


def test_generate_html_empty_details_and_top_offenders():
    """Testa casos limite: 0 details e 0 top_offenders."""
    report = get_mock_unified_report()
    report["details"] = []  # Covers line 114
    report["summary"]["top_offenders"] = []  # Covers line 84

    html_output = generate_html(report)

    # FIX 2: Corrected assertion for Top Offenders (no internal newline/tab in output)
    # The output is rendered as: <h3>Top Offenders</h3><p>None</p>
    assert "<h3>Top Offenders</h3><p>None</p>" in html_output

    # FIX 3: Corrected assertion for empty Details message
    # The output is rendered as: <h2>Details</h2>\n \t <p>No details available.</p>
    # Note: Using the exact string as generated in your exporters.py structure (includes newline before <p>)
    assert "<h2>Details</h2>\n    <p>No details available.</p>" in html_output

    # Ensure file/plugin details are NOT present
    assert "<h3>File:" not in html_output
    assert "<h4>Plugin:" not in html_output


def test_generate_html_no_issues_found_in_plugin():
    """Testa um plugin que correu mas não encontrou problemas (linha 177)."""
    report = get_mock_unified_report()
    report["details"] = [
        {
            "file": "clean_file.py",
            "plugins": [
                {
                    "plugin": "CleanP",
                    "summary": {"issues_found": 0, "status": "completed"},
                    "results": [],  # Empty results list to trigger line 177
                }
            ],
        }
    ]

    html_output = generate_html(report)

    # Check for the specific "No issues found" message (line 177 coverage)
    assert "<p><em>No issues found.</em></p>" in html_output
    assert "<li><strong>[LOW]</strong>" not in html_output # Ensure no issues were listed

# Note: The use of html.escape (line 164) is covered by the comprehensive report
# if the mock message contained characters like < or &
# Example: "message": "if a < b & c" should be asserted as "if a &lt; b &amp; c"