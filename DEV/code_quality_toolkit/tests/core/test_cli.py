import pytest

from src.toolkit.core.cli import _should_fail, SEVERITY_ORDER


def test_should_fail_returns_false_when_no_issues() -> None:
    report = {
        "summary": {
            "issues_by_severity": {"info": 0, "low": 0, "medium": 0, "high": 0},
            "total_issues": 0,
        }
    }
    assert _should_fail(report, "low") is False
    assert _should_fail(report, "medium") is False
    assert _should_fail(report, "high") is False


def test_should_fail_detects_issue_at_threshold() -> None:
    report = {
        "summary": {
            "issues_by_severity": {"info": 2, "low": 1, "medium": 0, "high": 0},
            "total_issues": 3,
        }
    }
    assert _should_fail(report, "low") is True
    assert _should_fail(report, "medium") is False
    assert _should_fail(report, "high") is False


def test_should_fail_detects_issue_above_threshold() -> None:
    report = {
        "summary": {
            "issues_by_severity": {"info": 0, "low": 0, "medium": 1, "high": 0},
            "total_issues": 1,
        }
    }
    assert _should_fail(report, "low") is True
    assert _should_fail(report, "medium") is True
    assert _should_fail(report, "high") is False


def test_should_fail_detects_high_severity() -> None:
    report = {
        "summary": {
            "issues_by_severity": {"info": 0, "low": 0, "medium": 0, "high": 1},
            "total_issues": 1,
        }
    }
    for threshold in SEVERITY_ORDER[:-1]:
        assert _should_fail(report, threshold) is True
    assert _should_fail(report, "high") is True


def test_should_fail_missing_severity_defaults_to_zero() -> None:
    report = {
        "summary": {
            "issues_by_severity": {"info": 1, "low": 0, "medium": 0},
            "total_issues": 1,
        }
    }
    assert _should_fail(report, "high") is False
