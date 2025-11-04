from textwrap import dedent

from toolkit.plugins.cyclomatic_complexity.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


def test_complexity_plugin_reports_high_complexity() -> None:
    source = dedent(
        """
        def sample(x):
            if x > 0:
                if x % 2 == 0:
                    return x
                else:
                    return -x
            return 0
        """
    )

    plugin = Plugin()
    config = ToolkitConfig()
    config.rules.max_complexity = 2
    plugin.configure(config)

    report = plugin.analyze(source, "sample.py")
    assert report["summary"]["issues_found"] == 1
    issue = report["results"][0]
    assert issue["code"] == "HIGH_COMPLEXITY"
