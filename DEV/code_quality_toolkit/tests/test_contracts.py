"""Testes para as funções de validação de contratos."""

import pytest

from toolkit.core import contracts

# CORREÇÃO: Este teste deve passar dados VÁLIDOS (o novo contrato)
def test_validate_plugin_report_accepts_valid_data() -> None:
    report = {
        "plugin": {"name": "Test", "version": "1.0", "author": "Test", "description": "Test"},
        "results": [
            {
                "file": "test.py",
                "entity": "N/A",
                "line": 1,
                "metric": "TEST_METRIC",
                "value": 10,
                "severity": "low",
                "message": "ok",
            }
        ],
        "summary": {"issues_found": 1, "status": "completed"},
    }
    contracts.validate_plugin_report(report)


def test_validate_plugin_report_rejects_missing_keys() -> None:
    # Este teste está correto, deve falhar
    with pytest.raises(ValueError, match="Missing key 'plugin'"):
        contracts.validate_plugin_report({"results": [], "summary": {}})


# CORREÇÃO: O 'valid_plugin' mock deve usar o novo contrato
def test_validate_unified_report_requires_metadata() -> None:
    valid_plugin = {
        "plugin": {"name": "Demo", "version": "1.0", "author": "Test", "description": "Test"},
        "results": [
            {
                "file": "demo.py",
                "entity": "N/A",
                "line": 1,
                "metric": "METRIC_A",
                "value": "N/A",
                "severity": "info",
                "message": "msg",
            }
        ],
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


# CORREÇÃO: Este teste estava a falhar (DID NOT RAISE)
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
            "issues_by_severity": {"info": 0, "low": 0, "medium": 0}, # 'high' em falta
            "issues_by_plugin": {},
            "top_offenders": [],
        },
        "details": [],
    }
    # Agora o 'contracts.py' deteta a falta da chave 'high' e levanta o erro
    with pytest.raises(ValueError, match="Missing severity key 'high'"):
        contracts.validate_unified_report(report)