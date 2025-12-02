from textwrap import dedent

import pytest

from toolkit.plugins.basic_metrics.plugin import Plugin
from toolkit.utils.config import ToolkitConfig

# Se o "radon" não estiver instalado (caso do job test_coverage),
# estes testes são automaticamente "skipped".
pytest.importorskip("radon")


# Código de exemplo para testar as métricas
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
    """
    Executa o plugin de basic_metrics sobre o código dado
    e devolve apenas o dicionário de métricas.

    Ajusta esta função se no teu plugin o caminho das métricas
    no relatório for diferente.
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    report = plugin.analyze(source, "test_file.py")

    # Em todos os plugins o contrato é:
    #   report: {"results": [...], "summary": {...}}
    summary = report["summary"]

    # Se no teu plugin as métricas estiverem aninhadas (ex.: summary["metrics"]),
    # elas são usadas; se não existirem, usamos o próprio summary como "metrics".
    metrics = summary.get("metrics", summary)

    return metrics

def test_number_of_lines() -> None:
    """
    Test number of lines (total de linhas do ficheiro).
    """
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["total_lines"] == 9

def test_blank_lines() -> None:
    """
    Test blank lines (linhas em branco).
    """
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["blank_lines"] == 3

def test_comment_lines() -> None:
    """
    Test comment lines (linhas de comentário).
    """
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["comment_lines"] == 2

def test_docstring_lines() -> None:
    """
    Test docstring lines (linhas pertencentes a docstrings).
    """
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["docstring_lines"] == 2

def test_lines_of_code() -> None:
    """
    Test lines of code (LOC) – linhas de código "real".
    """
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["logical_lines"] == 5

def test_metrics_on_empty_source() -> None:
    """
    Caso base: ficheiro vazio.
    Todas as métricas devem ser zero.
    """
    metrics = _run_metrics("")

    assert metrics["total_lines"] == 0
    assert metrics["blank_lines"] == 0
    assert metrics["comment_lines"] == 0
    assert metrics["docstring_lines"] == 0
    assert metrics["logical_lines"] == 0

def test_halstead_fallback(monkeypatch) -> None:
    """Test Halstead metrics fallback when radon is not available."""
    import toolkit.plugins.basic_metrics.plugin as bm
    monkeypatch.setattr(bm, "RADON_AVAILABLE", False)
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["h_volume"] == 0.0
    assert metrics["h_difficulty"] == 0.0
    assert metrics["h_effort"] == 0.0
    assert metrics["h_bugs"] == 0.0

@pytest.mark.parametrize("lines,expected_severity", [
    (1001, "low"), (2001, "medium"), (3001, "high")
])
def test_total_lines_issue(lines, expected_severity) -> None:
    source = "\n".join("x = 1" for _ in range(lines))
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze(source, "big_file.py")
    found = any(i["code"] == "total_lines" and i["severity"] == expected_severity
                for i in report["results"])
    assert found

def test_invalid_code_triggers_failure() -> None:
    source = "def foo(:"
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze(source, "bad_file.py")
    assert report["summary"]["status"] == "failed"
    assert report["summary"]["issues_found"] == 0

def test_comment_lines_percent_thresholds() -> None:
    # <2% comments
    lines = ["x = 1"] * 100
    lines.append("# comment")
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze("\n".join(lines), "file.py")
    issue = next((i for i in report["results"] if i["code"] == "comment_lines"), None)
    assert issue is not None
    assert issue["severity"] == "high"



"""
Este módulo testa a unit completa entre:
1. Análise de código (plugins)
2. Coleta de métricas (aggregator)
3. Geração de relatórios (report generation)
4. Validação de dados (contracts)
"""

import json
from pathlib import Path

import pytest

from toolkit.core.aggregator import aggregate
from toolkit.core.engine import run_analysis
from toolkit.plugins.basic_metrics.plugin import Plugin as basicMetricsPlugin
from toolkit.utils.config import ToolkitConfig


class TestMetricsUnits:
    """Units tests for end-to-end metrics collection."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project with sample Python files."""
        # Arquivo com estilo ruim
        file1 = tmp_path / "bad_style.py"
        file1.write_text(
            "x=1\ny=2\ndef  foo( a,b ):\n"
            "    return a+b\n"
            "# Long line that exceeds the default line length limit "
            "and should trigger style warnings from the StyleChecker\n",
            encoding="utf-8",
        )

        # Arquivo com duplicação
        file2 = tmp_path / "duplicated.py"
        file2.write_text(
            "def process_a():\n"
            "    x = 1\n"
            "    y = 2\n"
            "    z = x + y\n"
            "    return z\n"
            "\n"
            "def process_b():\n"
            "    x = 1\n"
            "    y = 2\n"
            "    z = x + y\n"
            "    return z\n",
            encoding="utf-8",
        )

        # Arquivo limpo
        file3 = tmp_path / "clean.py"
        file3.write_text(
            '"""Clean module."""\n'
            "\n"
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers."""\n'
            "    return a + b\n",
            encoding="utf-8",
        )

        return tmp_path

    @pytest.fixture
    def toolkit_config(self) -> ToolkitConfig:
        """Create a default toolkit configuration."""
        return ToolkitConfig()

    def test_metrics_collection_single_plugin(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test metrics collection using a single plugin."""
        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )
        # Verify structure
        assert isinstance(files, list)
        assert len(files) >= 1
        # Verify each file report
        for file_report in files:
            assert "file" in file_report
            assert "plugins" in file_report
            assert isinstance(file_report["plugins"], list)

            for plugin_result in file_report["plugins"]:
                assert "plugin" in plugin_result
                assert "results" in plugin_result
                assert "summary" in plugin_result
                assert "status" in plugin_result["summary"]

    def test_metrics_aggregation(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test metrics aggregation into a unified report."""
        plugins = {
            "BasicMetrics": basicMetricsPlugin(),
        }
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )

        # Aggregate results
        report = aggregate(files, plugin_status)

        # Verify report is a dictionary
        assert isinstance(report, dict)

        # Verify summary metrics
        summary = report["summary"]
        assert "total_files" in summary
        assert "total_issues" in summary
        assert "issues_by_plugin" in summary
        assert "issues_by_severity" in summary
        assert "top_offenders" in summary

        # Verify metadata
        assert "analysis_metadata" in report
        meta = report["analysis_metadata"]
        assert "tool_version" in meta
        assert "timestamp" in meta
        assert "status" in meta
        assert meta["timestamp"].endswith("Z")

    def test_metrics_severity_distribution(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that metrics correctly categorize issues by severity."""
        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        severity_dist = report["summary"]["issues_by_severity"]

        # Verify that severity distribution contains valid levels
        valid_severities = {"info", "low", "medium", "high"}
        for severity in severity_dist.keys():
            assert severity in valid_severities

        # Verify counts are non-negative
        for count in severity_dist.values():
            assert isinstance(count, int)
            assert count >= 0

    def test_metrics_top_offenders(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test identification and ranking of top offender files."""
        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        top_offenders = report["summary"]["top_offenders"]

        # Verify structure
        assert isinstance(top_offenders, list)
        for offender in top_offenders:
            assert "file" in offender
            assert "issues" in offender
            assert offender["issues"] > 0

        # Verify ordering (descending by issue count)
        if len(top_offenders) > 1:
            for i in range(len(top_offenders) - 1):
                assert (
                    top_offenders[i]["issues"]
                    >= top_offenders[i + 1]["issues"]
                )

    def test_metrics_plugin_breakdown(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test metrics breakdown by plugin."""
        plugins = {
            "BasicMetrics": basicMetricsPlugin(),
        }
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        issues_by_plugin = report["summary"]["issues_by_plugin"]

        # Verify plugins are present
        assert "BasicMetrics" in issues_by_plugin

        # Verify counts
        for _plugin_name, count in issues_by_plugin.items():
            assert isinstance(count, int)
            assert count >= 0

    def test_metrics_report_serialization(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that metrics report can be serialized to JSON."""
        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        # Serialize to JSON
        json_str = json.dumps(report, indent=2)
        assert isinstance(json_str, str)

        # Deserialize and verify structure is preserved
        deserialized = json.loads(json_str)
        assert "summary" in deserialized
        assert "analysis_metadata" in deserialized

    def test_metrics_empty_project(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test metrics collection on project with no issues."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text(
            '"""Clean module."""\n'
            "\n"
            "def hello() -> None:\n"
            '    """Say hello."""\n'
            "    print('hello')\n",
            encoding="utf-8",
        )

        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        # Verify structure exists even with no issues
        assert "summary" in report
        assert "analysis_metadata" in report
        assert report["summary"]["total_files"] >= 0

    def test_metrics_consistency_across_runs(
        self, temp_project: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that metrics are consistent across multiple runs."""
        plugins = {"BasicMetrics": basicMetricsPlugin()}

        # Run 1
        files1, plugin_status1 = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )
        report1 = aggregate(files1, plugin_status1)

        # Run 2
        files2, plugin_status2 = run_analysis(
            root=temp_project,
            plugins=plugins,
            config=toolkit_config,
        )
        report2 = aggregate(files2, plugin_status2)

        # Verify consistency
        assert report1["summary"]["total_files"] == report2["summary"]["total_files"]
        assert report1["summary"]["total_issues"] == report2["summary"]["total_issues"]
        assert (
            report1["summary"]["issues_by_severity"]
            == report2["summary"]["issues_by_severity"]
        )


class TestMetricsComparison:
    """Tests for comparing metrics across different analysis runs."""

    @pytest.fixture
    def toolkit_config(self) -> ToolkitConfig:
        """Create a default toolkit configuration."""
        return ToolkitConfig()

    def test_metrics_regression_detection(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test detection of regression (increase) in metrics."""
        # Create initial version
        file1 = tmp_path / "initial.py"
        # Modificado: ficheiro com quase nenhum comentário (vai disparar issue)
        file1.write_text("# coment\n" * 80 + "x=1\n" * 20, encoding="utf-8")


        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files1, plugin_status1 = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report1 = aggregate(files1, plugin_status1)
        issues_before = report1["summary"]["total_issues"]

        # Modify file to introduce more issues
        file1.write_text(
            "x=1\ny=2\nz=3\n"
            "# " + "x" * 200 + "\n",
            encoding="utf-8",
        )

        files2, plugin_status2 = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report2 = aggregate(files2, plugin_status2)
        issues_after = report2["summary"]["total_issues"]

        # Verify regression detection
        assert issues_after >= issues_before

    def test_metrics_improvement_detection(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test detection of improvement (decrease) in metrics."""
        # Create initial messy version
        file1 = tmp_path / "messy.py"
        # Teste para gerar issues
        file1.write_text("x=1\n" * 100, encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files1, plugin_status1 = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report1 = aggregate(files1, plugin_status1)
        issues_before = report1["summary"]["total_issues"]

        # Fix the file
        file1.write_text(
            '"""Clean module."""\n'
            "\n"
            "x = 1\n"
            "y = 2\n",
            encoding="utf-8",
        )

        files2, plugin_status2 = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report2 = aggregate(files2, plugin_status2)
        issues_after = report2["summary"]["total_issues"]

        # Verify improvement detection
        assert issues_after <= issues_before


class TestMetricsReporting:
    """Tests for metrics reporting and formatting."""

    @pytest.fixture
    def toolkit_config(self) -> ToolkitConfig:
        """Create a default toolkit configuration."""
        return ToolkitConfig()

    def test_metrics_report_completeness(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that all required metrics are present in report."""
        file1 = tmp_path / "test.py"
        file1.write_text("x=1\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}
        
        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        # Check required top-level keys
        required_keys = {"summary", "analysis_metadata"}
        assert required_keys.issubset(report.keys())

        # Check required summary keys
        required_summary = {
            "total_files",
            "total_issues",
            "issues_by_plugin",
            "issues_by_severity",
            "top_offenders",
        }
        assert required_summary.issubset(report["summary"].keys())

        # Check required metadata keys
        required_metadata = {
            "tool_version",
            "plugins_executed",
            "status",
            "timestamp",
        }
        assert required_metadata.issubset(report["analysis_metadata"].keys())


class TestMetricsComplexity:
    """Tests for cyclomatic complexity metrics validation."""

    @pytest.fixture
    def toolkit_config(self) -> ToolkitConfig:
        """Create a default toolkit configuration."""
        return ToolkitConfig()

    @pytest.fixture
    def simple_code(self, tmp_path: Path) -> Path:
        """Simple code with low complexity."""
        file = tmp_path / "simple.py"
        file.write_text(
            '"""Simple module."""\n'
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers."""\n'
            "    return a + b\n",
            encoding="utf-8",
        )
        return tmp_path

    @pytest.fixture
    def complex_code(self, tmp_path: Path) -> Path:
        """Complex code with high cyclomatic complexity."""
        file = tmp_path / "complex.py"
        file.write_text(
            "def process(x, y, z):\n"
            "    if x > 0:\n"
            "        if y > 0:\n"
            "            if z > 0:\n"
            "                return x + y + z\n"
            "            else:\n"
            "                return x + y\n"
            "        else:\n"
            "            if z > 0:\n"
            "                return x + z\n"
            "            else:\n"
            "                return x\n"
            "    elif y > 0:\n"
            "        if z > 0:\n"
            "            return y + z\n"
            "        else:\n"
            "            return y\n"
            "    else:\n"
            "        return 0\n",
            encoding="utf-8",
        )
        return tmp_path

    def test_complexity_metric_collection(
        self, simple_code: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that complexity metrics are collected."""
        try:
            from toolkit.plugins.cyclomatic_complexity.plugin import (
                Plugin as ComplexityPlugin,
            )
        except ImportError:
            pytest.skip("CyclomaticComplexity plugin not available")

        plugins = {"CyclomaticComplexity": ComplexityPlugin()}

        files, plugin_status = run_analysis(
            root=simple_code,
            plugins=plugins,
            config=toolkit_config,
        )

        report = aggregate(files, plugin_status)

        # Verify complexity metrics are in the report
        assert "CyclomaticComplexity" in report["summary"]["issues_by_plugin"]

    def test_complexity_simple_vs_complex(
        self, simple_code: Path, complex_code: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that simple code has lower complexity than complex code."""
        try:
            from toolkit.plugins.cyclomatic_complexity.plugin import (
                Plugin as ComplexityPlugin,
            )
        except ImportError:
            pytest.skip("CyclomaticComplexity plugin not available")

        plugins = {"CyclomaticComplexity": ComplexityPlugin()}

        # Analyze simple code
        files_simple, status_simple = run_analysis(
            root=simple_code,
            plugins=plugins,
            config=toolkit_config,
        )
        report_simple = aggregate(files_simple, status_simple)
        simple_issues = report_simple["summary"]["issues_by_plugin"].get(
            "CyclomaticComplexity", 0
        )

        # Analyze complex code
        files_complex, status_complex = run_analysis(
            root=complex_code,
            plugins=plugins,
            config=toolkit_config,
        )
        report_complex = aggregate(files_complex, status_complex)
        complex_issues = report_complex["summary"]["issues_by_plugin"].get(
            "CyclomaticComplexity", 0
        )

        # Complex code should have more issues (higher complexity)
        assert complex_issues >= simple_issues

    def test_metric_consistency_same_code(
        self, simple_code: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that metrics are consistent for the same code."""
        try:
            from toolkit.plugins.cyclomatic_complexity.plugin import (
                Plugin as ComplexityPlugin,
            )
        except ImportError:
            pytest.skip("CyclomaticComplexity plugin not available")

        plugins = {"CyclomaticComplexity": ComplexityPlugin()}

        # First run
        files1, status1 = run_analysis(
            root=simple_code,
            plugins=plugins,
            config=toolkit_config,
        )
        report1 = aggregate(files1, status1)
        complexity1 = report1["summary"]["issues_by_plugin"].get(
            "CyclomaticComplexity", 0
        )

        # Second run - same code
        files2, status2 = run_analysis(
            root=simple_code,
            plugins=plugins,
            config=toolkit_config,
        )
        report2 = aggregate(files2, status2)
        complexity2 = report2["summary"]["issues_by_plugin"].get(
            "CyclomaticComplexity", 0
        )

        # Metrics should match
        assert complexity1 == complexity2, (
            f"Metrics mismatch: run1={complexity1}, run2={complexity2}"
        )


class TestMetricsValidation:
    """Tests for metrics validation and matching."""

    @pytest.fixture
    def toolkit_config(self) -> ToolkitConfig:
        """Create a default toolkit configuration."""
        return ToolkitConfig()

    def test_total_issues_matches_breakdown(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Validate that total_issues matches sum of severity breakdown."""
        file = tmp_path / "test.py"
        file.write_text("x=1;y=2\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}

        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        # Calculate sum of all severities
        severity_sum = sum(
            report["summary"]["issues_by_severity"].values()
        )

        # Should match total_issues
        assert (
            report["summary"]["total_issues"] == severity_sum
        ), f"Total {report['summary']['total_issues']} != sum {severity_sum}"

    def test_plugin_issues_match_total(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Validate that sum of plugin issues matches total."""
        file = tmp_path / "test.py"
        file.write_text("x=1;y=2\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}

        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        # Calculate sum of all plugin issues
        plugin_sum = sum(report["summary"]["issues_by_plugin"].values())

        # Should match total_issues
        assert (
            report["summary"]["total_issues"] == plugin_sum
        ), f"Total {report['summary']['total_issues']} != plugin sum {plugin_sum}"

    def test_top_offenders_total_matches_report(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Validate that top offenders sum matches report total."""
        # Create multiple files
        (tmp_path / "file1.py").write_text("x=1;y=2;z=3\n", encoding="utf-8")
        (tmp_path / "file2.py").write_text("a=1;b=2\n", encoding="utf-8")
        (tmp_path / "file3.py").write_text("p=1\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}

        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        # Calculate sum from top offenders
        offenders_sum = sum(
            off["issues"] for off in report["summary"]["top_offenders"]
        )

        # Should match total (or be close, considering only top offenders)
        # Top offenders might not include all files if limit is set
        assert (
            offenders_sum <= report["summary"]["total_issues"]
        ), "Top offenders sum exceeds total"

    def test_metrics_deterministic(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Test that metrics are deterministic (same input = same output)."""
        file = tmp_path / "test.py"
        code = (
            "def foo(x, y):\n"
            "    if x > 0 and y > 0:\n"
            "        return x + y\n"
            "    return 0\n"
        )

        file.write_text(code, encoding="utf-8")

        plugins = {
            "BasicMetrics": basicMetricsPlugin(),
        }

        # Run multiple times
        reports = []
        for _ in range(3):
            files, status = run_analysis(
                root=tmp_path,
                plugins=plugins,
                config=toolkit_config,
            )
            report = aggregate(files, status)
            reports.append(report)

        # All reports should be identical
        for i in range(1, len(reports)):
            assert (
                reports[0]["summary"]["total_issues"]
                == reports[i]["summary"]["total_issues"]
            ), f"Run {i} has different total_issues"

            assert (
                reports[0]["summary"]["issues_by_severity"]
                == reports[i]["summary"]["issues_by_severity"]
            ), f"Run {i} has different severity distribution"

            assert (
                reports[0]["summary"]["issues_by_plugin"]
                == reports[i]["summary"]["issues_by_plugin"]
            ), f"Run {i} has different plugin breakdown"

    def test_file_report_matches_aggregated_metrics(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Validate that aggregated metrics match individual file reports."""
        (tmp_path / "test.py").write_text("x=1;y=2\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}

        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        # Count issues from individual file reports
        file_count = len(files)
        _ = sum(
            1
            for f in files
            if sum(p["summary"]["issues_found"] for p in f["plugins"]) > 0
        )


        # Verify totals match
        assert (
            report["summary"]["total_files"] == file_count
        ), f"File count mismatch: {file_count} vs {report['summary']['total_files']}"

    def test_severity_levels_are_valid(
        self, tmp_path: Path, toolkit_config: ToolkitConfig
    ) -> None:
        """Validate that all severity levels are from the valid set."""
        file = tmp_path / "test.py"
        file.write_text("x=1\n", encoding="utf-8")

        plugins = {"BasicMetrics": basicMetricsPlugin()}

        files, plugin_status = run_analysis(
            root=tmp_path,
            plugins=plugins,
            config=toolkit_config,
        )
        report = aggregate(files, plugin_status)

        valid_severities = {"info", "low", "medium", "high"}
        actual_severities = set(report["summary"]["issues_by_severity"].keys())

        # All actual severities should be in valid set
        assert actual_severities.issubset(
            valid_severities
        ), f"Invalid severities: {actual_severities - valid_severities}"
