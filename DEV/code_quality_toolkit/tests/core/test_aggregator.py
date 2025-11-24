from toolkit.core.aggregator import _derive_status, aggregate
from toolkit import __version__
from datetime import datetime


def test_derive_status_failed_when_empty() -> None:
    plugin_status = {}
    assert _derive_status(plugin_status) == "failed"


def test_derive_status_failed_if_any_failed() -> None:
    plugin_status = {
        "style": "completed",
        "security": "failed",
        "naming": "completed",
    }
    assert _derive_status(plugin_status) == "failed"

def test_derive_status_partial_if_any_partial_and_none_failed() -> None:
    plugin_status = {
        "style": "completed",
        "security": "partial",
        "naming": "completed",
    }
    assert _derive_status(plugin_status) == "partial"


def test_derive_status_completed_when_all_completed() -> None:
    plugin_status = {
        "style": "completed",
        "security": "completed",
        "naming": "completed",
    }
    assert _derive_status(plugin_status) == "completed"

def test_aggregate_computes_summary_metrics_and_metadata() -> None:
    # 3 files, 2 plugins each, severities mixed.
    files = [
        {
            "file": "a.py",
            "plugins": [
                {
                    "plugin": "StyleChecker",
                    "results": [
                        {"severity": "low", "code": "S1", "message": "x"},
                        {"severity": "medium", "code": "S2", "message": "y"},
                    ],
                    "summary": {"issues_found": 2, "status": "completed"},
                },
                {
                    "plugin": "SecurityChecker",
                    "results": [
                        {"severity": "high", "code": "SEC1", "message": "z"},
                    ],
                    "summary": {"issues_found": 1, "status": "completed"},
                },
            ],
        },
        {
            "file": "b.py",
            "plugins": [
                {
                    "plugin": "StyleChecker",
                    "results": [],
                    "summary": {"issues_found": 0, "status": "completed"},
                },
                {
                    "plugin": "SecurityChecker",
                    "results": [
                        {"severity": "low", "code": "SEC2", "message": "a"},
                        {"severity": "low", "code": "SEC3", "message": "b"},
                        {"severity": "medium", "code": "SEC4", "message": "c"},
                    ],
                    "summary": {"issues_found": 3, "status": "completed"},
                },
            ],
        },
        {
            "file": "c.py",
            "plugins": [
                {
                    "plugin": "StyleChecker",
                    "results": [
                        {"severity": "info", "code": "S3", "message": "i"},
                    ],
                    "summary": {"issues_found": 1, "status": "completed"},
                },
                {
                    "plugin": "SecurityChecker",
                    "results": [],
                    "summary": {"issues_found": 0, "status": "completed"},
                },
            ],
        },
    ]

    # força status global "partial"
    plugin_status = {
        "StyleChecker": "completed",
        "SecurityChecker": "partial",
    }

    report = aggregate(files, plugin_status)

    # ---- summary metrics ----
    assert report["summary"]["total_files"] == 3
    assert report["summary"]["total_issues"] == 7

    assert report["summary"]["issues_by_plugin"] == {
        "StyleChecker": 3,
        "SecurityChecker": 4,
    }

    assert report["summary"]["issues_by_severity"] == {
        "info": 1,
        "low": 3,
        "medium": 2,
        "high": 1,
    }

    assert report["summary"]["top_offenders"] == [
        {"file": "a.py", "issues": 3},
        {"file": "b.py", "issues": 3},
        {"file": "c.py", "issues": 1},
    ]

    # ---- analysis metadata ----
    meta = report["analysis_metadata"]
    assert meta["tool_version"] == __version__
    assert meta["plugins_executed"] == ["StyleChecker", "SecurityChecker"]
    assert meta["status"] == "partial"

    # timestamp ISO válido e termina em Z
    assert meta["timestamp"].endswith("Z")
    datetime.fromisoformat(meta["timestamp"][:-1])  # não deve lançar exceção
