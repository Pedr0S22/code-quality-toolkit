import pytest

from toolkit.core import contracts


def test_validate_plugin_report_accepts_valid_data() -> None:
    report = {
        "results": [{"severity": "low", "code": "X", "message": "ok"}],
        "summary": {"issues_found": 1, "status": "completed"},
    }
    contracts.validate_plugin_report(report)


def test_validate_plugin_report_rejects_missing_keys() -> None:
    with pytest.raises(ValueError):
        contracts.validate_plugin_report({"results": []})


def test_validate_unified_report_requires_metadata() -> None:
    valid_plugin = {
        "plugin": "Demo",
        "results": [{"severity": "info", "code": "A", "message": "msg"}],
        "summary": {"issues_found": 1, "status": "completed"},
    }
    report = {
        "analysis_metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "tool_version": "0.1.0",
            "plugins_executed": ["Demo"],
            "status": "completed",
        },
        "summary": {
            "total_files": 1,
            "total_issues": 1,
            "issues_by_severity": {"info": 1, "low": 0, "medium": 0, "high": 0},
            "issues_by_plugin": {"Demo": 1},
            "top_offenders": [{"file": "demo.py", "issues": 1}],
        },
        "details": [{"file": "demo.py", "plugins": [valid_plugin]}],
    }
    contracts.validate_unified_report(report)


def test_validate_unified_report_missing_severity_raises() -> None:
    report = {
        "analysis_metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "tool_version": "0.1.0",
            "plugins_executed": [],
            "status": "completed",
        },
        "summary": {
            "total_files": 0,
            "total_issues": 0,
            "issues_by_severity": {"info": 0, "low": 0, "medium": 0},
            "issues_by_plugin": {},
            "top_offenders": [],
        },
        "details": [],
    }
    with pytest.raises(ValueError):
        contracts.validate_unified_report(report)
