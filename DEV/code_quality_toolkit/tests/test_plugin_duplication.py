from textwrap import dedent

from toolkit.plugins.duplicate_code_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


def test_duplication_plugin_reports_duplicates() -> None:
    source = dedent(
        """
        def a():
            x = 1
            y = 2
            return x + y

        def b():
            x = 1
            y = 2
            return x + y
        """
    )

    plugin = Plugin()
    config = ToolkitConfig()
    plugin.configure(config)

    report = plugin.analyze(source, "sample.py")

    assert report["summary"]["issues_found"] > 0
    issue = report["results"][0]
    assert issue["code"] == "DUPLICATED_CODE"
