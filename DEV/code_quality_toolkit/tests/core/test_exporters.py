from toolkit.core.aggregator import aggregate


# --- Data of Complete Tests (To satisfy the validation) ---
def create_mock_result(severity="low", code="TEST001", count=1):
    """Ajuda a criar resultados que passam na validação rigorosa."""
    results = []
    for _ in range(count):
        results.append(
            {
                "severity": severity,
                "code": code,
                "message": "Mock error message",
                "line": 1,
                "col": 1,
            }
        )
    return {
        "results": results,
        "summary": {
            "issues_found": count,
            "status": "completed"  #Must have Field
        }
    }

# --- Tests ---

def test_aggregate_counts_total_issues_correctly():
    """Verifica a soma total de problemas."""
    mock_files = [
        {
            "file": "file_A.py",
            "plugins": [
                {
                    "plugin": "PluginA",
                    # now the whole dicionary
                    **create_mock_result("low", count=2)
                }
            ],
        },
        {
            "file": "file_B.py",
            "plugins": [{"plugin": "PluginB", **create_mock_result("high", count=1)}],
        },
    ]
    
    # Mock of the status of the plugins is also necessary
    mock_status = {"PluginA": "completed", "PluginB": "completed"}

    report = aggregate(mock_files, mock_status)

    assert report["summary"]["total_issues"] == 3


def test_aggregate_counts_by_severity_correctly():
    """Verifica a contagem por severidade."""
    
    # the mixed results manually created
    results_list = [
        {"severity": "high", "code": "T1", "message": "m"},
        {"severity": "medium", "code": "T2", "message": "m"},
        {"severity": "medium", "code": "T3", "message": "m"},
        {"severity": "low", "code": "T4", "message": "m"},
    ]

    mock_files = [
        {
            "file": "test.py",
            "plugins": [
                {
                    "plugin": "PluginA",
                    "results": results_list,
                    "summary": {"issues_found": 4, "status": "completed"},
                }
            ],
        }
    ]

    report = aggregate(mock_files, {"PluginA": "completed"})
    summary = report["summary"]

    assert summary["issues_by_severity"]["high"] == 1
    assert summary["issues_by_severity"]["medium"] == 2
    assert summary["issues_by_severity"]["low"] == 1
    assert summary["issues_by_severity"]["info"] == 0


def test_aggregate_counts_by_plugin_correctly():
    """Verifica a contagem por plugin."""
    mock_files = [
        {
            "file": "file1.py",
            "plugins": [{"plugin": "PluginA", **create_mock_result(count=1)}],
        },
        {
            "file": "file2.py",
            "plugins": [
                {"plugin": "PluginA", **create_mock_result(count=1)},
                {"plugin": "PluginB", **create_mock_result(count=3)},
            ],
        },
    ]

    report = aggregate(mock_files, {"PluginA": "completed", "PluginB": "completed"})
    summary = report["summary"]

    assert summary["issues_by_plugin"]["PluginA"] == 2
    assert summary["issues_by_plugin"]["PluginB"] == 3


def test_top_offenders_sorting_logic():
    """Verifica a ordenação dos piores ficheiros."""
    mock_files = [
        {
            "file": "clean.py",
            "plugins": [
                {
                    "plugin": "P1",
                    "results": [],
                    "summary": {"issues_found": 0, "status": "completed"},
                }
            ],
        },
        {
            "file": "worst_offender.py",
            "plugins": [{"plugin": "P1", **create_mock_result(count=50)}],
        },
        {
            "file": "bad_offender.py",
            "plugins": [{"plugin": "P1", **create_mock_result(count=5)}],
        },
    ]

    report = aggregate(mock_files, {"P1": "completed"})
    top = report["summary"]["top_offenders"]
    
    # The list must have at least 2 itens (the clean.py can be erased if the count > 0)
    assert len(top) >= 2
    assert top[0]["file"] == "worst_offender.py"
    assert top[0]["issues"] == 50

    assert top[1]["file"] == "bad_offender.py"
    assert top[1]["issues"] == 5
