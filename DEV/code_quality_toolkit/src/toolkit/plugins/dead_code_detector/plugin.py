"""Dead code detector plugin."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

PLUGIN_NAME = "dead_code_detector"


class _DefUseVisitor(ast.NodeVisitor):
    """Coleta definições e usos intra-ficheiro (escopo de módulo)."""

    def __init__(self) -> None:
        self.defs: dict[str, int] = {}
        self.uses: set[str] = set()
        self.imports: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defs[target.id] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.defs[node.target.id] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imports.add(alias.asname or alias.name)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.uses.add(node.id)
        self.generic_visit(node)


class Plugin:
    """Plugin que deteta 'dead code'."""

    def __init__(self) -> None:
        self.ignore_patterns: list[re.Pattern[str]] = [re.compile(r"^__")]
        self.severity: str = "low"
        self.min_name_length: int = 1
        # Internal stats to ensure we capture file paths even if engine strips them
        self._stats = {
            "affected_files": set(),
            "symbol_names": [],
        }

    def configure(self, config: ToolkitConfig) -> None:
        """Recebe parâmetros de [plugins.dead_code_detector] do toolkit.toml."""
        sect = getattr(getattr(config, "plugins", None), "dead_code_detector", None)
        if not sect:
            return
        pats = getattr(sect, "ignore_patterns", [])
        if isinstance(pats, list):
            compiled = [re.compile(p) for p in pats]
            if compiled:
                self.ignore_patterns = compiled
        self.severity = getattr(sect, "severity", self.severity)
        self.min_name_length = int(
            getattr(sect, "min_name_length", self.min_name_length)
        )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DeadCodeDetector",
            "version": "0.2.0",
            "description": "Deteta funções e variáveis não usadas no mesmo ficheiro.",
        }

    def _ignored(self, name: str) -> bool:
        if len(name) < self.min_name_length:
            return True
        for rx in self.ignore_patterns:
            if rx.search(name):
                return True
        return False

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Run the analysis on a single file and update internal stats."""
        try:
            results: list[IssueResult] = []
            try:
                tree = ast.parse(source_code)
            except SyntaxError as exc:
                results.append(
                    {
                        "severity": "high",
                        "code": "SYNTAX_ERROR",
                        "message": f"Erro de sintaxe: {exc}",
                        "line": exc.lineno or 0,
                        "col": exc.offset or 0,
                        "hint": "Corrija a sintaxe.",
                    }
                )
                return {
                    "results": results,
                    "summary": {"issues_found": len(results), "status": "partial"},
                }

            visitor = _DefUseVisitor()
            visitor.visit(tree)

            for name, line in visitor.defs.items():
                if self._ignored(name):
                    continue
                if name in visitor.imports:
                    continue
                if name not in visitor.uses:
                    msg = f"'{name}' definido e nunca usado."
                    results.append(
                        {
                            "severity": self.severity,
                            "code": "DEAD_CODE",
                            "message": msg,
                            "line": line or 1,
                            "col": 1,
                            "hint": "Remover ou utilizar.",
                        }
                    )
                    # Track for dashboard metrics
                    self._stats["symbol_names"].append(name) # type: ignore

            # Track file if issues found
            if len(results) > 0 and file_path:
                self._stats["affected_files"].add(str(file_path)) # type: ignore

            return {
                "results": results,
                "summary": {"issues_found": len(results), "status": "completed"},
            }

        except Exception as e:
            return {
                "results": [],
                "summary": {"issues_found": 0, "status": "failed", "error": str(e)},
            }

    def generate_dashboard(self, results: list[dict[str, Any]]) -> None:
        """
        Generate a D3.js dashboard using the confirmed working template.
        """
        try:
            # 1. Aggregate Data
            total_issues = len(results)
            severity_counts = {"info": 0, "low": 0, "medium": 0, "high": 0}

            # Count severities from the engine results
            for item in results:
                sev = item.get("severity", "low")
                if sev in severity_counts:
                    severity_counts[sev] += 1

            # Use internal stats for files and symbols to ensure availability
            affected_files = sorted(list(self._stats["affected_files"]))
            symbol_names = self._stats["symbol_names"]

            unique_symbols = len(set(symbol_names))
            avg_name_length = (
                sum(len(name) for name in symbol_names) / len(symbol_names)
                if symbol_names
                else 0.0
            )

            # 2. Prepare JSON Data
            dashboard_data = {
                "totalIssues": total_issues,
                "severityCounts": severity_counts,
                "affectedFiles": affected_files[:15],  # Limit to top 15
                "pluginMetrics": {
                    "uniqueSymbols": unique_symbols,
                    "avgNameLength": round(avg_name_length, 2),
                },
            }
            data_json = json.dumps(dashboard_data)

            # 3. HTML Template (The one confirmed to work)
            html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dead Code Detector Dashboard</title>
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
            margin-bottom: 20px;
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
            grid-template-rows: 1fr;
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
        .sev-info::before { background-color: #9cdcfe; }
        .sev-low::before { background-color: #4caf50; }
        .sev-medium::before { background-color: #ffb74d; }
        .sev-high::before { background-color: #f44336; }
    </style>
</head>
<body>
<div id="container">
    <h1>Dead Code Detector</h1>
    <div class="subtitle">
        Summary of unused functions, variables and classes detected in the project.
    </div>

    <div class="summary-row">
        <div class="card">
            <div class="card-title">Total Issues</div>
            <div class="card-value" id="total-issues">0</div>
        </div>
        <div class="card">
            <div class="card-title">Unique Symbols</div>
            <div class="card-value" id="unique-symbols">0</div>
            <div class="card-meta" id="avg-name-length">Avg. name length: 0</div>
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
                <span class="sev-info">Info</span>
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

    // Populate summary cards
    document.getElementById("total-issues").textContent =
        dashboardData.totalIssues;
    document.getElementById("unique-symbols").textContent =
        dashboardData.pluginMetrics.uniqueSymbols;
    document.getElementById("avg-name-length").textContent =
        "Avg. name length: " +
        dashboardData.pluginMetrics.avgNameLength.toFixed(2);
    document.getElementById("affected-files-count").textContent =
        dashboardData.affectedFiles.length;

    // Populate affected files list
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

    // Severity bar chart with D3
    const sevOrder = ["info", "low", "medium", "high"];
    const sevLabels = {
        info: "Info",
        low: "Low",
        medium: "Medium",
        high: "High"
    };
    const sevColors = {
        info: "#9cdcfe",
        low: "#4caf50",
        medium: "#ffb74d",
        high: "#f44336"
    };

    const severityData = sevOrder.map(function(s) {
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
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")");

    const x = d3.scaleBand()
        .domain(severityData.map(function(d) { return d.label; }))
        .range([0, innerWidth])
        .padding(0.25);

    const maxValue = d3.max(severityData, function(d) { return d.value; }) || 0;
    const y = d3.scaleLinear()
        .domain([0, maxValue === 0 ? 1 : maxValue])
        .range([innerHeight, 0]);

    const xAxis = d3.axisBottom(x);
    const yAxis = d3.axisLeft(y).ticks(4).tickFormat(d3.format("d"));

    g.append("g")
        .attr("transform", "translate(0," + innerHeight + ")")
        .attr("class", "x-axis")
        .call(xAxis)
        .selectAll("text")
        .attr("fill", "#d4d4d4")
        .style("font-size", "11px");

    g.append("g")
        .attr("class", "y-axis")
        .call(yAxis)
        .selectAll("text")
        .attr("fill", "#d4d4d4")
        .style("font-size", "11px");

    g.selectAll(".bar")
        .data(severityData)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", function(d) { return x(d.label); })
        .attr("y", function(d) { return y(d.value); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return innerHeight - y(d.value); })
        .attr("fill", function(d) { return sevColors[d.key]; });

    // Value labels on top of each bar
    g.selectAll(".bar-label")
        .data(severityData)
        .enter()
        .append("text")
        .attr("class", "bar-label")
        .attr("x", function(d) { return x(d.label) + x.bandwidth() / 2; })
        .attr("y", function(d) { return y(d.value) - 4; })
        .attr("text-anchor", "middle")
        .attr("fill", "#ffffff")
        .style("font-size", "11px")
        .text(function(d) { return d.value; });
</script>
</body>
</html>
"""

            # 4. Inject Data and Save
            html = html_template.replace("__DASHBOARD_DATA__", data_json)

            plugin_dir = Path(__file__).resolve().parent
            output_path = plugin_dir / "dead_code_detector_dashboard.html"
            output_path.write_text(html, encoding="utf-8")

        except Exception:
            return