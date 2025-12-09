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
            "total_issues": 0,
            "severity_counts": {"high": 0, "medium": 0, "low": 0, "info": 0},
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
            "version": "0.1.0",
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
                    # Track symbols for metrics
                    self._stats["symbol_names"].append(name)  # type: ignore

            # Update Internal Stats for Dashboard (Required)
            if len(results) > 0:
                self._stats["total_issues"] += len(results)
                if file_path:
                    self._stats["affected_files"].add(str(file_path))  # type: ignore
                for res in results:
                    sev = res.get("severity", "info")
                    if sev in self._stats["severity_counts"]:
                        self._stats["severity_counts"][sev] += 1  # type: ignore

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
        Generates the D3.js dashboard HTML file using the simplified template.
        """
        try:
            # 1. Prepare Data Payload
            # Transform severity counts into list for D3 binding:
            # e.g., [{'label': 'high', 'count': 5}, {'label': 'low', 'count': 2}]
            sev_data = [
                {"label": k, "count": v}
                for k, v in self._stats["severity_counts"].items()
            ]

            dashboard_data = {
                "total_issues": self._stats["total_issues"],
                "severity_counts": sev_data,
                # Convert set to list for JSON serialization
                "affected_files": list(self._stats["affected_files"]),
                "plugin_metrics": {
                    "unique_symbols": len(set(self._stats["symbol_names"]))
                },
            }

            data_json = json.dumps(dashboard_data)

            # 2. HTML Template (Simplified Version per Documentation)
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <title>Plugin Dashboard</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 20px; }}
        .chart-container {{
            width: 1066px;
            height: 628px;
            border: 1px solid #ddd;
            margin: auto;
        }}
    </style>
</head>
<body>

<div id="app" class="chart-container">
    <h2 style="text-align:center; padding-top:10px;">Dead Code Analysis</h2>
</div>

<script>
    // Data injected from Python
    const data = {data_json};

    // Initialize SVG with mandatory dimensions
    const svg = d3.select("#app")
        .append("svg")
        .attr("width", 1066)
        .attr("height", 628);

    // Render Bar Chart if data exists
    if (data.severity_counts) {{
        const margin = {{ top: 50, right: 30, bottom: 50, left: 50 }};
        const width = 1066 - margin.left - margin.right;
        const height = 550 - margin.top - margin.bottom;

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Basic scale for positioning
        const x = d3.scaleBand()
            .domain(data.severity_counts.map(d => d.label))
            .range([0, width])
            .padding(0.4);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data.severity_counts, d => d.count) || 10])
            .range([height, 0]);

        // Draw Bars
        g.selectAll("rect")
            .data(data.severity_counts)
            .enter()
            .append("rect")
            .attr("x", d => x(d.label))
            .attr("y", d => y(d.count))
            .attr("width", x.bandwidth())
            .attr("height", d => height - y(d.count))
            .attr("fill", d => {{
                if(d.label === 'high') return '#dc3545';
                if(d.label === 'medium') return '#ffc107';
                return '#28a745';
            }});

        // Add Labels
        g.selectAll("text.label")
            .data(data.severity_counts)
            .enter()
            .append("text")
            .text(d => d.count)
            .attr("x", d => x(d.label) + x.bandwidth()/2)
            .attr("y", d => y(d.count) - 5)
            .attr("text-anchor", "middle")
            .style("font-size", "14px");

        // Add Axes
        g.append("g")
            .attr("transform", `translate(0, ${{height}})`)
            .call(d3.axisBottom(x))
            .style("font-size", "14px");

        g.append("g")
            .call(d3.axisLeft(y));
    }}
</script>

</body>
</html>"""

            # 3. Save to Disk
            # Use resolve().parent to find the directory of the current plugin file
            plugin_dir = Path(__file__).resolve().parent
            output_path = plugin_dir / "dead_code_detector_dashboard.html"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"Dashboard generated: {output_path}")

        except Exception as e:
            # Ensure dashboard failure doesn't crash the main engine
            print(f"Failed to generate dashboard: {e}")
