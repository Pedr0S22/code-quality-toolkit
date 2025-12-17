"""Plugin que procura por codigo duplicado."""

from __future__ import annotations

import json
import subprocess  # nosec B404 - uso controlado
import sys
from pathlib import Path
from typing import Any

from ...utils.config import ToolkitConfig


class Plugin:
    def __init__(self) -> None:
        self.min_name_length = 10

    def configure(self, config: ToolkitConfig) -> None:
        """Recebe parâmetros de [plugins.duplication_checker] do toolkit.toml."""
        sect = getattr(getattr(config, "plugins", None), "duplication_checker", None)
        if not sect:
            return
        self.min_name_length = int(
            getattr(sect, "min_name_length", self.min_name_length)
        )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DuplicationChecker",
            "version": "0.1.0",
            "description": "Detects duplicated code using pylint R0801",
        }

    # ------------------------------------------------------------------
    # Analyze
    # ------------------------------------------------------------------

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        if not file_path:
            return {"error": "file_path required"}

        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Invalid path: {file_path}")

        # If it's a directory, gather all .py files
        if path_obj.is_dir():
            files_to_check = [str(p) for p in path_obj.rglob("*.py")]
        else:
            files_to_check = [str(path_obj)]

        if not files_to_check:
            return {
                "plugin": self.get_metadata()["name"],
                "results": [],
                "summary": {"issues_found": 0, "status": "completed"},
            }

        # Run pylint on all files at once
        proc = subprocess.run(  # nosec B603
            [
                sys.executable,
                "-m",
                "pylint",
                "--disable=all",
                "--enable=R0801",
                *files_to_check,
            ],
            capture_output=True,
            text=True,
        )

        results = []
        for line in proc.stdout.splitlines():
            try:
                path_part, line_part, col_part, rest = line.split(":", 3)
                row = int(line_part)
                col = int(col_part)
                code = "R0801"
                message = rest.strip()
            except (ValueError, IndexError):
                continue

            results.append(
                {
                    "plugin": self.get_metadata()["name"],
                    "file": path_part,
                    "entity": "bloco duplicado",
                    "line_numbers": [row],
                    "similarity": 100,
                    "refactoring_suggestion": "Consolidar bloco",
                    "details": {"occurrences": 1, "message": message},
                    "metric": "duplicate_code",
                    "value": None,
                    "severity": "medium",
                    "code": code,
                    "message": message,
                    "line": row,
                    "col": col,
                    "hint": "Refactor to remove repeated logic.",
                }
            )

        summary = {"issues_found": len(results), "status": "completed"}

        results = {
            "plugin": self.get_metadata()["name"],
            "results": results,
            "summary": summary,
        }

        return results

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def generate_dashboard(self, results):
        """
        Generates the D3.js dashboard HTML file.
        """
        dashboard_file = "src/toolkit/plugins/duplication_checker/"
        dashboard_file += "duplication_checker_dashboard.html"

        html_content = self.render_html(results)

        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def render_html(self, results) -> str:
        """
        Prepares data and returns the final HTML dashboard.
        """
        dashboard_data = self._aggregate_data_for_dashboard(results)
        data_json = json.dumps(dashboard_data)
        return self._get_html_template(data_json)

    def _aggregate_data_for_dashboard(self, results):
        """
        Aggregates duplication results into a dashboard-friendly structure.
        """
        rule_code = "DUPLICATED_CODE"

        file_counts = {}
        total_issues = 0

        # Unwrap results list if passed in the new format
        items = results.get("results", []) if isinstance(results, dict) else results

        for item in items:
            path = item.get("path") or item.get("file")
            if not path:
                continue
            file_counts[path] = file_counts.get(path, 0) + 1
            total_issues += 1

        top_files = [
            {
                "file": path,
                "count": count,
                "type": rule_code,
            }
            for path, count in sorted(
                file_counts.items(),
                key=lambda x: x[1],
                reverse=True)
        ][:10]

        return {
            "metrics": {
                "total_files": len(file_counts),
                "total_issues": total_issues,
            },
            "rule_counts": [
                {"code": rule_code, "count": total_issues}
            ],
            "top_files": top_files,
        }

    def _get_html_template(self, data_json: str) -> str:
        """Template D3.js Responsivo (Blue Theme)."""
        # noqa: E501
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Duplicate Code Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>

<div id="app" class="chart-container"></div>

<script>
    const data = {data_json};
    const width = 1066;
    const height = 628;

    const svg = d3.select("#app")
        .append("svg")
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "100%")
        .style("background-color", "#fff");

    svg.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", width)
        .attr("height", 70)
        .attr("fill", "#0d6efd");

    svg.append("text")
        .attr("x", 20)
        .attr("y", 45)
        .attr("fill", "white")
        .style("font-size", "24px")
        .style("font-weight", "bold")
        .text("Duplicate Code Analysis");

    const mGroup = svg.append("g")
        .attr("transform", "translate(750, 20)");

    mGroup.append("rect")
        .attr("width", 140)
        .attr("height", 30)
        .attr("rx", 5)
        .attr("fill", "rgba(255,255,255,0.2)");

    mGroup.append("text")
        .attr("x", 70)
        .attr("y", 20)
        .attr("text-anchor", "middle")
        .attr("fill", "white")
        .style("font-weight", "bold")
        .text(
            `Files w/ Duplicates: `
            + `${{data.metrics.total_files}}`
        );

    mGroup.append("rect")
        .attr("x", 150)
        .attr("width", 140)
        .attr("height", 30)
        .attr("rx", 5)
        .attr("fill", "rgba(255,255,255,0.2)");

    mGroup.append("text")
        .attr("x", 220)
        .attr("y", 20)
        .attr("text-anchor", "middle")
        .attr("fill", "white")
        .style("font-weight", "bold")
        .text(
            `Total Duplications: `
            + `${{data.metrics.total_issues}}`
        );

    const col1X = 50;
    const col2X = 550;
    const contentY = 120;

    svg.append("text")
        .attr("x", col1X)
        .attr("y", contentY - 10)
        .style("font-size", "18px")
        .style("font-weight", "bold")
        .text("Reference");

    const defGroup = svg.append("g")
        .attr(
            "transform",
            `translate(${{col1X}}, ${{contentY}})`
        );

    const definitions = [
        {{
            code: "DUPLICATED_CODE",
            color: "#dc3545",
            title: "Duplicated Code",
            desc:
                "Identical or near-identical code blocks "
                + "found across files."
        }}
    ];

    definitions.forEach((def, i) => {{
        const y = i * 80;

        defGroup.append("rect")
            .attr("width", 450)
            .attr("height", 70)
            .attr("rx", 5)
            .attr("fill", "#f8f9fa")
            .attr("stroke", "#eee");

        defGroup.append("rect")
            .attr("width", 5)
            .attr("height", 70)
            .attr("fill", def.color);

        defGroup.append("text")
            .attr("x", 15)
            .attr("y", 25)
            .style("font-weight", "bold")
            .text(def.title + " (" + def.code + ")");

        defGroup.append("text")
            .attr("x", 15)
            .attr("y", 50)
            .style("font-size", "13px")
            .attr("fill", "#666")
            .text(def.desc);
    }});

    const rulesY = contentY + 240;

    svg.append("text")
        .attr("x", col1X)
        .attr("y", rulesY - 10)
        .style("font-size", "18px")
        .style("font-weight", "bold")
        .text("Violation Counts");

    const ruleGroup = svg.append("g")
        .attr(
            "transform",
            `translate(${{col1X + 160}}, ${{rulesY}})`
        );

    const ruleData = data.rule_counts || [];

    if (ruleData.length) {{
        const max = d3.max(ruleData, d => d.count);

        const x = d3.scaleLinear()
            .domain([0, max * 1.2])
            .range([0, 290]);

        const y = d3.scaleBand()
            .domain(ruleData.map(d => d.code))
            .range([0, 80])
            .padding(0.2);

        ruleGroup.append("g")
            .call(d3.axisLeft(y));

        ruleGroup.selectAll("rect")
            .data(ruleData)
            .enter()
            .append("rect")
            .attr("y", d => y(d.code))
            .attr("height", y.bandwidth())
            .attr("width", d => x(d.count))
            .attr("fill", "#0d6efd");
    }}

    svg.append("text")
        .attr("x", col2X)
        .attr("y", contentY - 10)
        .style("font-size", "18px")
        .style("font-weight", "bold")
        .text("Files with Most Duplications");

    const listGroup = svg.append("g")
        .attr(
            "transform",
            `translate(${{col2X}}, ${{contentY}})`
        );

    listGroup.append("rect")
        .attr("width", 450)
        .attr("height", 420)
        .attr("fill", "#fafafa")
        .attr("stroke", "#eee");

    const offenders = data.top_files || [];

    if (offenders.length) {{
        offenders.forEach((file, i) => {{
            const y = 30 + i * 40;

            listGroup.append("text")
                .attr("x", 15)
                .attr("y", y)
                .style("font-family", "monospace")
                .style("font-size", "12px")
                .text(`${{i + 1}}. ${{file.file}}`);

            listGroup.append("rect")
                .attr("x", 400)
                .attr("y", y - 12)
                .attr("width", 30)
                .attr("height", 18)
                .attr("rx", 4)
                .attr("fill", "#6c757d");

            listGroup.append("text")
                .attr("x", 415)
                .attr("y", y + 1)
                .attr("text-anchor", "middle")
                .attr("fill", "white")
                .style("font-size", "11px")
                .style("font-weight", "bold")
                .text(file.count);
        }});
    }} else {{
        listGroup.append("text")
            .attr("x", 225)
            .attr("y", 210)
            .attr("text-anchor", "middle")
            .attr("fill", "#28a745")
            .style("font-size", "16px")
            .text("✅ No duplicated code found!");
    }}
</script>
</body>
</html>"""
