from src.toolkit.core.aggregator import _derive_status


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