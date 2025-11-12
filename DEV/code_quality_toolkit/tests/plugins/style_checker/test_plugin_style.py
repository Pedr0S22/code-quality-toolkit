from toolkit.plugins.style_checker.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


def test_style_checker_flags_long_line() -> None:
    plugin = Plugin()
    config = ToolkitConfig()
    config.rules.max_line_length = 10
    plugin.configure(config)

    report = plugin.analyze("linha muito longa", "sample.py")

    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]
    assert issue["code"] == "LINE_LENGTH"
