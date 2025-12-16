import os
from textwrap import dedent

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


def test_render_html():

    fake_results = { 
     "results": [],
     "summary": {
         "issues_found": 0,
         "status": "completed",
         "metrics": {
             "total_lines": 10,
             "logical_lines": 5,
             },
         },
     }

    plugin = Plugin()
    html_output = plugin.render_html(fake_results)
    assert isinstance(html_output, str)
    assert "total_lines" in html_output


def test_generate_dashboard(tmp_path):
    plugin = Plugin()
    results = {
        "results": [],
        "summary": {
            "issues_found": 0,
            "status": "completed",
            "metrics": {"total_lines": 1},
        },
    }

    # Create expected directory structure
    assets_dir = tmp_path / "src" / "toolkit" / "plugins" / "basic_metrics"
    assets_dir.mkdir(parents=True)

    # Run from tmp_path so relative paths resolve correctly
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        plugin.generate_dashboard(results)
    finally:
        os.chdir(cwd)

    dashboard_file = assets_dir / "plugin_basic_metrics_dashboard.html"
    assert dashboard_file.exists()

    content = dashboard_file.read_text()
    assert "total_lines" in content
