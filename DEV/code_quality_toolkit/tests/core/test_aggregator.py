"""Unit tests for the Results Aggregator (Task #177)."""

from toolkit.core.aggregator import _derive_status, aggregate

# --- Testes existentes (_derive_status) ---


def test_derive_status_failed_when_empty() -> None:
    plugin_status = {}
    assert _derive_status(plugin_status) == "failed"


def test_derive_status_partial_if_any_failed_and_some_completed() -> None:
    plugin_status = {
        "style": "completed",
        "security": "failed",
        "naming": "completed",
    }
    assert _derive_status(plugin_status) == "partial"


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


# --- NOVO: Teste da função principal aggregate ---


def test_aggregate_creates_correct_structure():
    """Testa se a função aggregate gera o relatório unificado corretamente."""

    # 1. Arrange: Dados simulados vindos do Engine
    files_data = [
        {
            "file": "main.py",
            "plugins": [
                {
                    "plugin": "StyleChecker",
                    "summary": {"issues_found": 1, "status": "completed"},
                    "results": [
                        # Nota: Usamos a estrutura do contracts.py (code, hint)
                        {
                            "severity": "low",
                            "code": "TEST_CODE",
                            "message": "Test msg",
                            "line": 1,
                            "col": 1,
                            "hint": "Fix it",
                        }
                    ],
                }
            ],
        }
    ]

    plugin_status = {"StyleChecker": "completed"}

    # 2. Act
    report = aggregate(files_data, plugin_status)

    # 3. Assert: Verificar estrutura do UnifiedReport

    # Metadados
    assert report["analysis_metadata"]["status"] == "completed"
    assert "StyleChecker" in report["analysis_metadata"]["plugins_executed"]

    # Sumário Global
    summary = report["summary"]
    assert summary["total_files"] == 1
    assert summary["total_issues"] == 1
    assert summary["issues_by_severity"]["low"] == 1
    assert summary["issues_by_severity"]["high"] == 0

    # Verificar contagem por plugin
    assert summary["issues_by_plugin"]["StyleChecker"] == 1

    # Verificar detalhes
    assert len(report["details"]) == 1
    assert report["details"][0]["file"] == "main.py"
