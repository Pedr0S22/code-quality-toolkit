import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

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

    assert "plugin" in report
    assert "summary" in report
    assert "results" in report
    
    for issue in report["results"]:
        print(issue)  # Isto mostra todas as chaves disponíveis


    for issue in report["results"]:
        for field in[
            "file",
            "entity",
            "line_numbers",
            "details",
            "metric",
            "value",
            "severity",
            "message",
        ]:
            assert field in issue
        assert issue ["file"] == "sample.py"
        assert issue["severity"] in {"low", "medium", "high"}
        assert issue["metric"] == "duplicate_code"
        # line_numbers should be a list of ints (one or more occurrences)
        assert isinstance(issue["line_numbers"], list)
        assert all(isinstance(n, int) for n in issue["line_numbers"])
        assert report["summary"]["issues_found"] == len(report["results"]) - 1  # Exclude the summary entry


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

    # Now check returns grouped entries: signature, lines, block, occurrences
    assert len(results) > 0
    assert all("signature" in r and "lines" in r and r["occurrences"] > 1 for r in results)


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
    issue=report["results"][0]
    for issue in report["results"]:
        print(issue)
        print("----")
        print(f"Linha: {issue['line']} -- Mensagem: {issue['message']}")
        #assert issue["code"] == "DUPLICATED_CODE"
       
        assert "severity" in issue
        assert issue["severity"] in {"low", "medium", "high"}
        
        #assert issue["col"] == 0
        #assert "hint" in issue
        assert isinstance(issue["line"], int)
        
        #assert "metric" in issue
        assert issue["metric"] == "duplicate_code"
        assert "value" in issue
        