"""Cyclomatic complexity plugin with a lightweight heuristic."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


def _function_length(node: ast.AST) -> int | None:
    """Calcula o numero de linhas em funcao."""
    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        return node.end_lineno - node.lineno + 1
    return None


def _arg_count(fn: ast.AST) -> int:
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return 0
    a = fn.args
    total = 0
    total += len(getattr(a, "posonlyargs", []))
    total += len(a.args)
    total += len(a.kwonlyargs)
    total += 1 if a.vararg else 0
    total += 1 if a.kwarg else 0
    return total


class _ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1

    def generic_visit(self, node: ast.AST) -> None:  # noqa: D401 - inherited docs
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.With,
                ast.BoolOp,
                ast.And,
                ast.Or,
                ast.ExceptHandler,
            ),
        ):
            self.complexity += 1
        super().generic_visit(node)


class Plugin:
    """Calcula complexidade ciclomática aproximada por função."""

    def __init__(self) -> None:
        self.max_complexity = 10
        self.max_function_length = 50
        self.max_arguments = 5
        self._stats = {
            "affected_files": set(),
        }


    def configure(self, config: ToolkitConfig) -> None:
        """Update plugin thresholds from new [plugins.cyclomatic_complexity] section."""

        # Access the new configuration section [plugins.cyclomatic_complexity]
        sect = getattr(
            getattr(config, "plugins", None),
            "cyclomatic_complexity",
            None
        )

        # Use the section if found, otherwise stick to defaults
        if sect:
            # All rules are now defined under the plugin section
            self.max_complexity = getattr(
                sect, "max_complexity", self.max_complexity
            )
            self.max_function_length = getattr(
                sect, "max_function_length", self.max_function_length
            )
            self.max_arguments = getattr(
                sect, "max_arguments", self.max_arguments
            )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "CyclomaticComplexity",
            "version": "0.2.0",
            "description": "Conta decisões em funções para estimar complexidade.",
        }

    def generate_dashboard(self, results: list[dict[str, Any]]) -> None:
        """
        Generates the D3.js Cyclomatic Complexity dashboard HTML file.
        Must be standalone, 1066x628, D3 v7+, and must not raise exceptions.
        """
        try:
            # 1) Aggregate required data
            total_issues = len(results)

            # Only High/Medium/Low required by issue
            severity_counts = {"low": 0, "medium": 0, "high": 0}
            for item in results:
                sev = str(item.get("severity", "low")).lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1

            affected_files = sorted(list(self._stats["affected_files"]))  # type: ignore

            # 2) Plugin-specific metrics (extract from messages when possible)
            # Issue codes in this plugin:
            #HIGH_COMPLEXITY, LONG_FUNCTION, TOO_MANY_ARGUMENTS, SYNTAX_ERROR
            code_counts: dict[str, int] = {}
            complexities: list[int] = []
            lengths: list[int] = []
            arg_counts: list[int] = []

            rx_complexity = re.compile(r"complexidade\s+(\d+)", re.IGNORECASE)
            rx_lines = re.compile(r"\((\d+)\s+lines\)", re.IGNORECASE)
            rx_args = re.compile(r"\((\d+)\s+arguments\)", re.IGNORECASE)

            for item in results:
                code = str(item.get("code", "UNKNOWN"))
                code_counts[code] = code_counts.get(code, 0) + 1

                msg = str(item.get("message", ""))

                m = rx_complexity.search(msg)
                if m:
                    complexities.append(int(m.group(1)))

                m = rx_lines.search(msg)
                if m:
                    lengths.append(int(m.group(1)))

                m = rx_args.search(msg)
                if m:
                    arg_counts.append(int(m.group(1)))

            def _avg(nums: list[int]) -> float:
                return (sum(nums) / len(nums)) if nums else 0.0

            plugin_metrics = {
                "highComplexityCount": code_counts.get("HIGH_COMPLEXITY", 0),
                "longFunctionCount": code_counts.get("LONG_FUNCTION", 0),
                "tooManyArgsCount": code_counts.get("TOO_MANY_ARGUMENTS", 0),
                "avgReportedComplexity": round(_avg(complexities), 2),
                "maxReportedComplexity": max(complexities) if complexities else 0,
                "avgFunctionLengthLines": round(_avg(lengths), 2),
                "avgArgCount": round(_avg(arg_counts), 2),
            }

            dashboard_data = {
                "totalIssues": total_issues,
                "severityCounts": severity_counts,
                "affectedFiles": affected_files[:15],  # top 15
                "pluginMetrics": plugin_metrics,
            }
            data_json = json.dumps(dashboard_data)

            # 3) Standalone HTML template (D3 v7+), strict 1066x628 container
            html_template = """<!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8" />
        <title>Cyclomatic Complexity Dashboard</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background-color: #1e1e1e;
            color: #d4d4d4;
            }
            #container {
            width: 1066px;
            height: 628px;
            box-sizing: border-box;
            padding: 20px;
            background-color: #1e1e1e;
            }
            h1 {
            margin: 0 0 10px 0;
            color: #4ec9b0;
            font-size: 22px;
            }
            .subtitle {
            margin-bottom: 16px;
            color: #9cdcfe;
            font-size: 13px;
            }
            .summary-row {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            }
            .card {
            flex: 1;
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 6px;
            padding: 10px 14px;
            box-sizing: border-box;
            }
            .card-title {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #808080;
            margin-bottom: 6px;
            }
            .card-value {
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            }
            .card-meta {
            font-size: 11px;
            color: #a0a0a0;
            margin-top: 4px;
            }
            #layout {
            display: grid;
            grid-template-columns: 2fr 1.4fr;
            gap: 16px;
            height: calc(628px - 110px);
            }
            #severity-chart-container, #files-container {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 6px;
            padding: 12px 16px;
            box-sizing: border-box;
            overflow: hidden;
            }
            #severity-chart-title, #files-title {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #808080;
            margin-bottom: 8px;
            }
            #files-list {
            font-size: 12px;
            line-height: 1.4;
            max-height: 100%;
            overflow-y: auto;
            }
            #files-list ul {
            padding-left: 18px;
            margin: 0;
            }
            #files-list li {
            margin-bottom: 4px;
            color: #dcdcdc;
            }
            .sev-legend {
            font-size: 11px;
            margin-top: 6px;
            color: #a0a0a0;
            }
            .sev-legend span {
            display: inline-flex;
            align-items: center;
            margin-right: 12px;
            }
            .sev-legend span::before {
            content: "";
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 2px;
            margin-right: 4px;
            }
            .sev-low::before { background-color: #4caf50; }
            .sev-medium::before { background-color: #ffb74d; }
            .sev-high::before { background-color: #f44336; }
        </style>
        </head>
        <body>
        <div id="container">
        <h1>Cyclomatic Complexity</h1>
        <div class="subtitle">
            Summary of complexity-related issues detected in the project.
        </div>

        <div class="summary-row">
            <div class="card">
            <div class="card-title">Total Issues</div>
            <div class="card-value" id="total-issues">0</div>
            </div>
            <div class="card">
            <div class="card-title">High Complexity</div>
            <div class="card-value" id="high-complexity">0</div>
            <div class="card-meta" id="complexity-meta">Avg complexity: 0</div>
            </div>
            <div class="card">
            <div class="card-title">Affected Files</div>
            <div class="card-value" id="affected-files-count">0</div>
            <div class="card-meta">Top files listed on the right</div>
            </div>
        </div>

        <div id="layout">
            <div id="severity-chart-container">
            <div id="severity-chart-title">Issues by severity</div>
            <svg id="severity-chart" width="640" height="360"></svg>
            <div class="sev-legend">
                <span class="sev-low">Low</span>
                <span class="sev-medium">Medium</span>
                <span class="sev-high">High</span>
            </div>
            </div>
            <div id="files-container">
            <div id="files-title">Affected files (up to 15)</div>
            <div id="files-list"></div>
            </div>
        </div>
        </div>

        <script>
        const dashboardData = __DASHBOARD_DATA__;

        document.getElementById("total-issues").textContent = dashboardData.totalIssues;
        document.getElementById("high-complexity").textContent =
            dashboardData.pluginMetrics.highComplexityCount;

        document.getElementById("complexity-meta").textContent =
            "Avg complexity: " + dashboardData.pluginMetrics.avgReportedComplexity +
            " | Max: " + dashboardData.pluginMetrics.maxReportedComplexity +
            " | Long funcs: " + dashboardData.pluginMetrics.longFunctionCount +
            " | Too many args: " + dashboardData.pluginMetrics.tooManyArgsCount;

        document.getElementById("affected-files-count").textContent =
            dashboardData.affectedFiles.length;

        // Files list
        const filesDiv = document.getElementById("files-list");
        if (dashboardData.affectedFiles.length === 0) {
            filesDiv.textContent = "No file information available.";
        } else {
            const ul = document.createElement("ul");
            dashboardData.affectedFiles.forEach(function (file) {
            const li = document.createElement("li");
            li.textContent = file;
            ul.appendChild(li);
            });
            filesDiv.appendChild(ul);
        }

        // Severity chart (D3)
        const sevOrder = ["low", "medium", "high"];
        const sevLabels = { low: "Low", medium: "Medium", high: "High" };
        const sevColors = { low: "#4caf50", medium: "#ffb74d", high: "#f44336" };

        const severityData = sevOrder.map(function (s) {
            return { 
                key: s,
                label: sevLabels[s],
                value: dashboardData.severityCounts[s] || 0 
            };
        });

        const svg = d3.select("#severity-chart");
        const width = +svg.attr("width");
        const height = +svg.attr("height");

        const margin = { top: 30, right: 20, bottom: 40, left: 40 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        const g = svg.append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        const x = d3.scaleBand()
            .domain(severityData.map(function (d) { return d.label; }))
            .range([0, innerWidth])
            .padding(0.25);

        const maxValue = d3.max(severityData, function (d) { return d.value; }) || 0;
        const y = d3.scaleLinear()
            .domain([0, maxValue === 0 ? 1 : maxValue])
            .range([innerHeight, 0]);

        g.append("g")
            .attr("transform", "translate(0," + innerHeight + ")")
            .call(d3.axisBottom(x))
            .selectAll("text")
            .attr("fill", "#d4d4d4")
            .style("font-size", "11px");

        g.append("g")
            .call(d3.axisLeft(y).ticks(4).tickFormat(d3.format("d")))
            .selectAll("text")
            .attr("fill", "#d4d4d4")
            .style("font-size", "11px");

        g.selectAll(".bar")
            .data(severityData)
            .enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", function (d) { return x(d.label); })
            .attr("y", function (d) { return y(d.value); })
            .attr("width", x.bandwidth())
            .attr("height", function (d) { return innerHeight - y(d.value); })
            .attr("fill", function (d) { return sevColors[d.key]; });

        g.selectAll(".bar-label")
            .data(severityData)
            .enter()
            .append("text")
            .attr("class", "bar-label")
            .attr("x", function (d) { return x(d.label) + x.bandwidth() / 2; })
            .attr("y", function (d) { return y(d.value) - 4; })
            .attr("text-anchor", "middle")
            .attr("fill", "#ffffff")
            .style("font-size", "11px")
            .text(function (d) { return d.value; });
        </script>
        </body>
        </html>
        """

            # 4) Inject data and save in required location/name
            html = html_template.replace("__DASHBOARD_DATA__", data_json)
            plugin_dir = Path(__file__).resolve().parent
            output_path = plugin_dir / "cyclomatic_complexity_dashboard.html"
            output_path.write_text(html, encoding="utf-8")

        except Exception:
            return



    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Run the analysis on a single file.
        This function MUST NOT raise an exception.
        """

        try:
            # SyntaxError logic
            try:
                tree = ast.parse(source_code)
            except SyntaxError as exc:
                return {
                    "results": [
                        {
                            "severity": "high",
                            "code": "SYNTAX_ERROR",
                            "message": f"Erro de sintaxe: {exc}",
                            "line": exc.lineno or 0,
                            "col": exc.offset or 0,
                            "hint": "Corrija a sintaxe antes de medir complexidade.",
                        }
                    ],
                    "summary": {"issues_found": 1, "status": "partial"},
                }

            results: list[IssueResult] = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visitor = _ComplexityVisitor()
                    visitor.visit(node)
                    complexity = visitor.complexity
                    if complexity > self.max_complexity:
                        severity = (
                            "medium"
                            if complexity <= self.max_complexity + 4
                            else "high"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "HIGH_COMPLEXITY",
                                "message": f"Função '{node.name}' com complexidade "
                                + f"{complexity}",
                                "line": node.lineno,
                                "col": 0,
                                "hint": f"Reduza para <= {self.max_complexity}",
                            }
                        )
                    function_length = _function_length(node)
                    if (
                        function_length is not None
                        and function_length > self.max_function_length
                    ):
                        severity = (
                            "low"
                            if function_length <= self.max_function_length + 20
                            else "medium"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "LONG_FUNCTION",
                                "message": f"Function '{node.name}' with "
                                + f"({function_length} lines)",
                                "line": node.lineno,
                                "col": 0,
                                "hint": "Consider dividing to smaller functions "
                                + f"(<= {self.max_function_length} lines).",
                            }
                        )
                    arg_count = _arg_count(node)
                    if arg_count > self.max_arguments:
                        severity = (
                            "low" if arg_count <= self.max_arguments + 2 else "medium"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "TOO_MANY_ARGUMENTS",
                                "message": f"Function '{node.name}' with "
                                + f"({arg_count} arguments)",
                                "line": node.lineno,
                                "col": 0,
                                "hint": "Consider reducing number of arguments "
                                + f"(<= {self.max_arguments}).",
                            }
                        )

            if results and file_path:
                self._stats["affected_files"].add(str(file_path))

            # Return a standard Success Response
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        # This 'except' block  catches any other unexpected behaviour
        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }
