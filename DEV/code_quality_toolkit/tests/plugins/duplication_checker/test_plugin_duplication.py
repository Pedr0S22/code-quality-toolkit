from textwrap import dedent

from toolkit.plugins.duplicate_code_checker.plugin import DuplicateCodeChecker, Plugin
from toolkit.utils.config import ToolkitConfig

""" --- Integration Tests --- """


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


""" --- Unit Tests --- """


def test_duplicate_code_checker_finds_duplicates():
    src = dedent(
        """
        a = 1
        b = 2
        c = a + b

        a = 1
        b = 2
        c = a + b
        """
    )

    dc = DuplicateCodeChecker()
    results = dc.check(src)

    assert len(results) > 0
    assert all(r["code"] == "DUPLICATED_CODE" for r in results)


def test_duplicate_code_checker_no_duplicates():
    src = dedent(
        """
        x = 1
        y = 2
        z = x * y
        """
    )

    dc = DuplicateCodeChecker()
    results = dc.check(src, window=2)

    assert results == []


def test_plugin_analyze_wraps_results():
    src = dedent(
        """
        a = 1
        b = 2
        c = a + b

        a = 1
        b = 2
        c = a + b
        """
    )

    plugin = Plugin()
    report = plugin.analyze(src, "file.py")

    assert report["summary"]["issues_found"] > 0
    assert any(r["code"] == "DUPLICATED_CODE" for r in report["results"])
    assert report["summary"]["status"] == "completed"
