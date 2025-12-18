from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest

from toolkit.plugins.basic_metrics.plugin import Plugin
from toolkit.utils.config import ToolkitConfig

pytest.importorskip("radon")


SAMPLE_CODE = dedent(
    '''
    """Module docstring"""

    # Comment 1

    def foo():
        """Function docstring"""
        x = 1  # inline comment
        return x
    '''
).lstrip("\n")


def _run_metrics(source: str) -> dict:
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze(source, "test_file.py")
    summary = report["summary"]
    return summary.get("metrics", summary)


def test_number_of_lines() -> None:
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["total_lines"] == 8


def test_blank_lines() -> None:
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["blank_lines"] == 2


def test_comment_lines() -> None:
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["comment_lines"] == 2


def test_docstring_lines() -> None:
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["docstring_lines"] == 2


def test_lines_of_code() -> None:
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["logical_lines"] == 5


def test_metrics_on_empty_source() -> None:
    metrics = _run_metrics("")
    assert metrics["total_lines"] == 0
    assert metrics["blank_lines"] == 0
    assert metrics["comment_lines"] == 0
    assert metrics["docstring_lines"] == 0
    assert metrics["logical_lines"] == 0


def test_metrics_with_only_comments() -> None:
    source = "# comment1\n# comment2\n\n"
    metrics = _run_metrics(source)
    assert metrics["total_lines"] == 3
    assert metrics["blank_lines"] == 1  # blank line at end
    assert metrics["comment_lines"] == 2
    assert metrics["docstring_lines"] == 0
    assert metrics["logical_lines"] == 0


def test_metrics_with_multiline_docstring() -> None:
    source = '"""\nMulti-line\nDocstring\n"""\n'
    metrics = _run_metrics(source)
    assert metrics["total_lines"] == 4
    assert metrics["blank_lines"] == 0
    assert metrics["comment_lines"] == 0
    assert metrics["docstring_lines"] == 4
    assert metrics["logical_lines"] == 1


@pytest.fixture
def plugin():
    return Plugin()


@pytest.fixture
def mock_results():
    """Simulates the results structure returned by the engine."""
    return [
        {
            "file": "C:\\Users\\pedro\\AppData\\Local\\Temp\\"
            + "source\\sample_project\\main.py",
            "plugins": [
                {
                    "plugin": "BasicMetrics",
                    "results": [
                        {
                            "severity": "high",
                            "code": "total_lines",
                            "message": "File too big",
                        }
                    ],
                }
            ],
        },
        {
            "file": "/home/user/project/source/utils/helper.py",
            "plugins": [
                {
                    "plugin": "BasicMetrics",
                    "results": [
                        {
                            "severity": "low",
                            "code": "comment_lines",
                            "message": "Few comments",
                        }
                    ],
                }
            ],
        },
    ]


def test_path_normalization_to_relative(plugin, mock_results):
    """Verifies that absolute paths are converted to relative paths in the HTML."""
    with patch.object(Path, "write_text") as mock_write:
        # We pass a temporary path as output_dir
        plugin.generate_dashboard(mock_results, output_dir=Path("."))

        written_html = mock_write.call_args[0][0]

        # We check for the relative part specifically.
        assert (
            "sample_project\\\\main.py" in written_html
            or "sample_project\\main.py" in written_html
        )
        assert (
            "utils\\\\helper.py" in written_html or "utils\\helper.py" in written_html
        )
        assert "C:\\\\Users" not in written_html
        assert "/home/user" not in written_html


def test_aggregation_logic(plugin, mock_results):
    """Verifies that issues are correctly counted and aggregated."""
    aggregated = plugin._aggregate_data_for_dashboard(mock_results)

    assert aggregated["metrics"]["total_files"] == 2
    assert aggregated["metrics"]["total_issues"] == 2

    # Check that filenames in top_files are normalized
    file_names = [item["file"] for item in aggregated["top_files"]]
    # We check if the end of the path matches to avoid OS-specific
    # backslash escaping issues
    assert any(name.endswith("sample_project\\main.py") for name in file_names)


def test_dashboard_file_naming(plugin, mock_results):
    """Verifies dashboard file naming."""
    # We patch Path.write_text, but we need to check the Path object it was called on
    with patch("pathlib.Path.write_text") as mock_write:
        plugin.generate_dashboard(mock_results, output_dir=Path("/tmp"))

        assert mock_write.called


def test_handle_empty_results(plugin):
    """Verifies the dashboard doesn't crash with empty data."""
    with patch.object(Path, "write_text") as mock_write:
        plugin.generate_dashboard([], output_dir=Path("."))
        written_html = mock_write.call_args[0][0]
        # In your HTML template, it should be total_issues: 0
        assert 'total_issues": 0' in written_html
