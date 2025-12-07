"""Simple style checking plugin."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

_SNAKE_CASE_RE = re.compile(r"^[a-z0-9_]+\.py$")
_TRAILING_WS_RE = re.compile(r"[ \t]+$")
_LEADING_WS_RE = re.compile(r"^([ \t]+)")
_CLASS_NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_FUNC_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class Plugin:
    """Plugin que valida regras de estilo básicas."""

    def __init__(self) -> None:
        self.max_line_length = 88
        self.check_whitespace = True
        self.indent_style = "spaces"
        self.indent_size = 4
        self.allow_mixed_indentation = False
        self.check_naming = False

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""

        self.max_line_length = config.rules.max_line_length
        self.check_whitespace = config.rules.check_whitespace
        self.indent_style = config.rules.indent_style
        self.indent_size = config.rules.indent_size
        self.allow_mixed_indentation = config.rules.allow_mixed_indentation
        self.check_naming = config.rules.check_naming

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "style_checker",
            "version": "0.1.3",
            "description": "Valida comprimento de linhas, convenções simples"
            " de nomes, trailingwhitespace, identation e naming convention.",
        }

    def _check_trailing_whitespace(self, lines: list[str]) -> list[IssueResult]:
        results: list[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            m = _TRAILING_WS_RE.search(line)
            if m:
                col = m.start() + 1
                results.append(
                    {
                        "severity": "low",
                        "code": "TRAILING_WHITESPACE",
                        "message": "Espaços ou tabulações no final da linha.",
                        "line": idx,
                        "col": col,
                        "hint": "Remova os espaços/tabulações no final.",
                    }
                )
        return results

    def _check_indentation(self, lines: list[str]) -> list[IssueResult]:
        results: list[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            if not line:
                continue

            m = _LEADING_WS_RE.match(line)
            if not m:
                continue

            leading = m.group(1)
            has_tab = "\t" in leading
            has_space = " " in leading

            if has_tab and has_space and not self.allow_mixed_indentation:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_MIXED",
                        "message": "Mistura de tabulações e"
                        " espaços no início da linha.",
                        "line": idx,
                        "col": 1,
                        "hint": "Utilize apenas um estilo: defina o ficheiro"
                        " rules.indent_style e ajuste o seu editor.",
                    }
                )

            if self.indent_style == "spaces" and has_tab:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_TABS_NOT_ALLOWED",
                        "message": "Os recuos com tabulações não são permitidos"
                        " (os espaços são obrigatórios).",
                        "line": idx,
                        "col": 1,
                        "hint": f"Converter tabulações em espaços"
                        f" (múltiplos de {self.indent_size}).",
                    }
                )

                continue

            if self.indent_style == "tabs" and has_space:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_SPACES_NOT_ALLOWED",
                        "message": "Não são permitidos recuos "
                        "com espaços (tabulações são obrigatórias).",
                        "line": idx,
                        "col": 1,
                        "hint": "Converter espaços em tabulações para criar avanços.",
                    }
                )
                continue

            if self.indent_style == "spaces" and has_space and not has_tab:
                width = len(leading)
                if width % self.indent_size != 0:
                    results.append(
                        {
                            "severity": "low",
                            "code": "INDENT_WIDTH",
                            "message": f"O recuo não é um múltiplo"
                            f" de espaços {self.indent_size}.",
                            "line": idx,
                            "col": 1,
                            "hint": f"Ajuste o recuo para "
                            f"múltiplos de {self.indent_size}.",
                        }
                    )

        return results

    def _check_naming_conventions(
        self, source_code: str, file_path: str | None
    ) -> list[IssueResult]:
        results: list[IssueResult] = []

        try:
            tree = ast.parse(source_code, filename=file_path or "<unknown>")
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not _CLASS_NAME_RE.match(node.name):
                    results.append(
                        {
                            "severity": "low",
                            "code": "CLASS_NAMING",
                            "message": f"Class name '{node.name}'"
                            f" deve usar o CamelCase.",
                            "line": node.lineno,
                            "col": node.col_offset + 1,
                            "hint": "Utilize nomes como 'MyClass', 'UserProfile', etc.",
                        }
                    )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not _FUNC_NAME_RE.match(node.name):
                    results.append(
                        {
                            "severity": "low",
                            "code": "FUNC_NAMING",
                            "message": f"Function name '{node.name}'"
                            f" deve usar o snake_case.",
                            "line": node.lineno,
                            "col": node.col_offset + 1,
                            "hint": "Utilize nomes como "
                            "'process_data', 'get_user', etc.",
                        }
                    )

        return results

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        try:
            results: list[IssueResult] = []
            lines = source_code.splitlines()
            for idx, line in enumerate(lines, start=1):
                if len(line) > self.max_line_length:
                    results.append(
                        {
                            "severity": "low",
                            "code": "LINE_LENGTH",
                            "message": f"Linha com {len(line)} caracteres",
                            "line": idx,
                            "col": 1,
                            "hint": f"Máximo configurado: {self.max_line_length}",
                        }
                    )

            if self.check_whitespace:
                results.extend(self._check_trailing_whitespace(lines))

            results.extend(self._check_indentation(lines))

            if self.check_naming:
                results.extend(self._check_naming_conventions(source_code, file_path))

            if file_path and not _SNAKE_CASE_RE.match(Path(file_path).name):
                results.append(
                    {
                        "severity": "info",
                        "code": "FILENAME_STYLE",
                        "message": "Nome do ficheiro não segue snake_case.",
                        "line": 1,
                        "col": 1,
                        "hint": "Utilize nomes como sample_module.py",
                    }
                )
            
            if file_path:
                for issue in results:
                    issue.setdefault("file", str(file_path))

            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        except Exception as e:
            # Captura de errores para evitar crash do plugin
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }
        
    def generate_dashboard(self, results: list[IssueResult]) -> None:
        """
        Generate a D3.js HTML dashboard for the StyleChecker plugin.

        This method is called by the engine AFTER all files were analyzed.
        The 'results' argument contains ALL issues for this plugin across all files.
        """
        plugin_folder = Path(__file__).parent

        # NOTE:
        # According to the spec, the dashboard file name must be:
        #   <plugin_name>_dashboard.html
        # and plugin_name must be snake_case.
        # We hardcode "style_checker" here to ensure the correct format.
        plugin_name = "style_checker"

        dashboard_file = plugin_folder / f"{plugin_name}_dashboard.html"

        # Total number of issues reported by this plugin
        total_issues = len(results)

        # Count issues by severity (low, medium, high, info, etc.)
        severity_counts_map: dict[str, int] = {}
        for issue in results:
            severity = issue.get("severity", "unknown")
            severity_counts_map[severity] = severity_counts_map.get(severity, 0) + 1

        severity_counts = [
            {"severity": sev, "count": count}
            for sev, count in sorted(severity_counts_map.items())
        ]

        # Count issues by rule/code (e.g. LINE_LENGTH, TRAILING_WHITESPACE)
        rule_counts_map: dict[str, int] = {}
        for issue in results:
            code = issue.get("code", "UNKNOWN")
            rule_counts_map[code] = rule_counts_map.get(code, 0) + 1

        rule_counts = [
            {"code": code, "count": count}
            for code, count in sorted(
                rule_counts_map.items(), key=lambda x: x[1], reverse=True
            )
        ]

        # Optional: Top files by number of issues.
        # This requires each issue to have a "file" key.
        files_map: dict[str, int] = {}
        for issue in results:
            file_path = issue.get("file")
            if file_path:
                files_map[file_path] = files_map.get(file_path, 0) + 1

        top_files = [
            {"file": file_path, "count": count}
            for file_path, count in sorted(
                files_map.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        # Data object that will be injected into the HTML as JSON
        data = {
            "plugin": "StyleChecker",
            "total_issues": total_issues,
            "severity_counts": severity_counts,
            "rule_counts": rule_counts,
            "top_files": top_files,
        }

        data_json = json.dumps(data)

        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StyleChecker Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            padding: 20px;
        }
        .chart-container {
            width: 1066px;
            height: 628px;
            border: 1px solid #ddd;
            box-sizing: border-box;
        }
    </style>
</head>
<body>

<!-- Main container for the dashboard -->
<div id="app" class="chart-container"></div>

<script>
    // Data injected from Python (JSON literal)
    const data = __DATA_JSON__;

    const width = 1066;
    const height = 628;

    // Create main SVG canvas with required dimensions
    const svg = d3.select("#app")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // ---- Header / title ----
    svg.append("text")
        .attr("x", 20)
        .attr("y", 30)
        .style("font-size", "16px")
        .style("font-weight", "bold")
        .text("StyleChecker - Dashboard");

    // ---- Summary line (e.g. total issues) ----
    const summaryText = `Total issues: ${data.total_issues}`;
    svg.append("text")
        .attr("x", 20)
        .attr("y", 55)
        .style("font-size", "12px")
        .text(summaryText);

    // ---------- Helper function: reusable bar chart ----------
    function drawBarChart(group, dataset, xKey, yKey, title, chartWidth, chartHeight) {
        // If no data, display a simple message
        if (!dataset || dataset.length === 0) {
            group.append("text")
                .attr("x", 0)
                .attr("y", 15)
                .style("font-size", "12px")
                .text("No data available");
            return;
        }

        // X scale: categorical (band) based on xKey (severity or rule code)
        const x = d3.scaleBand()
            .domain(dataset.map(d => d[xKey]))
            .range([0, chartWidth])
            .padding(0.2);

        // Y scale: linear, based on counts
        const y = d3.scaleLinear()
            .domain([0, d3.max(dataset, d => d[yKey]) || 0])
            .nice()
            .range([chartHeight, 0]);

        // X axis (bottom)
        group.append("g")
            .attr("transform", `translate(0,${chartHeight})`)
            .call(d3.axisBottom(x))
            .selectAll("text")
            .style("font-size", "10px")
            .attr("transform", "rotate(-30)")
            .style("text-anchor", "end");

        // Y axis (left)
        group.append("g")
            .call(d3.axisLeft(y).ticks(5))
            .selectAll("text")
            .style("font-size", "10px");

        // Bars
        group.selectAll("rect")
            .data(dataset)
            .enter()
            .append("rect")
            .attr("x", d => x(d[xKey]))
            .attr("y", d => y(d[yKey]))
            .attr("width", x.bandwidth())
            .attr("height", d => chartHeight - y(d[yKey]))
            .attr("fill", "#3b82f6");  // basic blue color

        // Chart title
        group.append("text")
            .attr("x", 0)
            .attr("y", -10)
            .style("font-weight", "bold")
            .style("font-size", "12px")
            .text(title);
    }

    // ---------- Chart 1: Issues by severity ----------
    const severityGroup = svg.append("g")
        .attr("transform", "translate(60, 100)");

    drawBarChart(
        severityGroup,
        data.severity_counts,
        "severity",
        "count",
        "Issues by severity",
        400,
        180
    );

    // ---------- Chart 2: Issues by rule/code ----------
    const rulesGroup = svg.append("g")
        .attr("transform", "translate(560, 100)");

    // Only show top 8 rules to avoid label clutter
    const topRules = (data.rule_counts || []).slice(0, 8);

    drawBarChart(
        rulesGroup,
        topRules,
        "code",
        "count",
        "Issues by rule",
        400,
        180
    );

    // ---------- Section: Top files (text list) ----------
    const filesGroup = svg.append("g")
        .attr("transform", "translate(60, 340)");

    filesGroup.append("text")
        .attr("x", 0)
        .attr("y", 0)
        .style("font-weight", "bold")
        .style("font-size", "12px")
        .text("Top files (by number of StyleChecker issues)");

    if (data.top_files && data.top_files.length > 0) {
        data.top_files.forEach((d, i) => {
            filesGroup.append("text")
                .attr("x", 0)
                .attr("y", 20 + i * 16)
                .style("font-size", "11px")
                .text(`${i + 1}. ${d.file} (${d.count})`);
        });
    } else {
        filesGroup.append("text")
            .attr("x", 0)
            .attr("y", 20)
            .style("font-size", "11px")
            .text("No file-level data available.");
    }
</script>

</body>
</html>
"""

        # Replace the placeholder with the actual JSON string
        html_content = html_template.replace("__DATA_JSON__", data_json)

        # Finally, write the HTML content to disk
        dashboard_file.write_text(html_content, encoding="utf-8")

