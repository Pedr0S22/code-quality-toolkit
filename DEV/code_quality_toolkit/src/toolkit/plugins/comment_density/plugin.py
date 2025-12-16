import ast
import json
from pathlib import Path
from typing import Any

from toolkit.utils.config import ToolkitConfig


class Plugin:
    """
    Comment Density Analyzer Plugin.
    Gera Dashboard D3.js Responsivo (Blue Theme).
    """

    def __init__(self) -> None:
        self.min_density = 0.1  # 10%
        self.max_density = 0.5  # 50%
        self.config = None

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin with rules"""
        self.config = config
        self.min_density = getattr(config.rules, "min_density", 0.1)
        self.max_density = getattr(config.rules, "max_density", 0.5)

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "CommentDensity",
            "version": "0.3.4",
            "description": "Analyzes comment density violations (D3.js Dashboard).",
        }

    def _count_lines(self, source: str) -> tuple[int, int]:
        lines = source.split("\n")
        code_lines = 0
        comment_lines = 0
        in_multiline_comment = False
        multiline_comment_char = None

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            if in_multiline_comment:
                comment_lines += 1
                if multiline_comment_char in stripped_line:
                    if (
                        stripped_line.endswith(multiline_comment_char)
                        or stripped_line.count(multiline_comment_char) >= 2
                    ):
                        in_multiline_comment = False
                continue

            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                comment_lines += 1
                multiline_comment_char = stripped_line[:3]
                if (
                    stripped_line.endswith(multiline_comment_char)
                    and len(stripped_line) > 3
                    and stripped_line.count(multiline_comment_char) == 2
                ):
                    in_multiline_comment = False
                else:
                    in_multiline_comment = True
                continue

            if "#" in stripped_line:
                parts = stripped_line.split("#", 1)
                code_part = parts[0].strip()
                comment_part = parts[1] if len(parts) > 1 else ""

                if code_part:
                    code_lines += 1
                if comment_part:
                    comment_lines += 1
                elif not code_part:
                    comment_lines += 1
            else:
                code_lines += 1

        return code_lines, comment_lines

    def analyze(self, source: str, filename: str) -> dict[str, Any]:
        """Analyze comment density in source code"""
        try:
            non_empty_lines = [line for line in source.splitlines() if line.strip()]
            if len(non_empty_lines) < 5:
                return {
                    "results": [],
                    "summary": {
                        "issues_found": 0,
                        "status": "completed",
                        "metrics": {
                            "code_lines": len(non_empty_lines),
                            "comment_lines": 0,
                            "total_lines": len(non_empty_lines),
                            "comment_density": 0.0,
                        },
                    },
                }

            ast.parse(source)

            code_lines, comment_lines = self._count_lines(source)
            total_lines = code_lines + comment_lines
            density = comment_lines / total_lines if total_lines > 0 else 0

            issues = []

            if density < self.min_density:
                issues.append(
                    {
                        "line": 1,
                        "column": 0,
                        "message": (
                            f"Low comment density: {density:.1%} "
                            f"(min: {self.min_density:.1%})"
                        ),
                        "code": "LOW_COMMENT_DENSITY",
                        "severity": "high",
                        "hint": "Add documentation",
                    }
                )
            elif density > self.max_density:
                issues.append(
                    {
                        "line": 1,
                        "column": 0,
                        "message": (
                            f"High comment density: {density:.1%} "
                            f"(max: {self.max_density:.1%})"
                        ),
                        "code": "HIGH_COMMENT_DENSITY",
                        "severity": "high",
                        "hint": "Simplify comments",
                    }
                )

            for issue in issues:
                issue["file"] = filename

            return {
                "results": issues,
                "summary": {
                    "issues_found": len(issues),
                    "status": "completed",
                    "metrics": {
                        "code_lines": code_lines,
                        "comment_lines": comment_lines,
                        "density": density,
                        "comment_density": density,  # Mantido para testes
                    },
                },
            }

        except Exception as exc:
            return {
                "results": [],
                "summary": {"issues_found": 0, "status": "failed", "error": str(exc)},
            }

    # ==========================================================================
    # DASHBOARD GENERATION
    # ==========================================================================

    def generate_dashboard(
        self,
        aggregated_results: list[dict],
        output_path: str = "comment_density_dashboard.html",
        dependency_data: dict = None,
    ) -> str:
        """Gera o dashboard."""

        dashboard_data = self._aggregate_data_for_dashboard(aggregated_results)

        # Injetamos as configurações para a legenda
        dashboard_data["thresholds"] = {
            "min": f"{self.min_density:.0%}",
            "max": f"{self.max_density:.0%}",
        }

        # print(
        #     f"[CommentDensity] Dashboard: "
        #     f"{dashboard_data['metrics']['total_issues']} violações encontradas."
        # )

        data_json = json.dumps(dashboard_data)
        html_content = self._get_html_template(data_json)

        try:
            target_path = Path(output_path)
            if not target_path.is_absolute():
                output_dir = Path(__file__).parent
                output_file = output_dir / target_path
            else:
                output_file = target_path

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_content, encoding="utf-8")
            return str(output_file.absolute())
        except Exception:
            # print(f"[CommentDensity] Erro ao salvar dashboard: {e}")
            return ""

    def _aggregate_data_for_dashboard(self, results: list[dict]) -> dict:
        flattened_issues = []

        # Normalização (File Reports -> Flat List)
        for entry in results:
            if "plugins" in entry:
                file_path = entry.get("file", "unknown")
                plugins_list = entry.get("plugins", [])

                plugin_res = next(
                    (p for p in plugins_list if p["plugin"] == "CommentDensity"), None
                )
                if plugin_res:
                    issues = plugin_res.get("results", [])
                    for issue in issues:
                        if "file" not in issue:
                            issue["file"] = file_path
                        flattened_issues.append(issue)

            elif "code" in entry or "severity" in entry:
                flattened_issues.append(entry)

        # Contagem
        rule_counts = {}
        files_counter = {}

        for issue in flattened_issues:
            code = issue.get("code", "UNKNOWN")
            rule_counts[code] = rule_counts.get(code, 0) + 1

            fname = issue.get("file", "unknown")

            # Se o arquivo ainda não existe no contador, cria
            if fname not in files_counter:
                files_counter[fname] = {"count": 0, "type": code}

            files_counter[fname]["count"] += 1
            # Atualiza o tipo (HIGH sobrescreve LOW)
            if "HIGH" in code:
                files_counter[fname]["type"] = code

        rule_data = [{"code": k, "count": v} for k, v in rule_counts.items()]
        rule_data.sort(key=lambda x: x["count"], reverse=True)

        # Formata lista de arquivos para o D3
        top_files = [
            {"file": k, "count": v["count"], "type": v["type"]}
            for k, v in files_counter.items()
        ]
        top_files.sort(key=lambda x: x["count"], reverse=True)

        return {
            "metrics": {
                "total_files": len(files_counter),
                "total_issues": len(flattened_issues),
            },
            "rule_counts": rule_data,
            "top_files": top_files[:10],
        }

    def _get_html_template(self, data_json: str) -> str:
        """Template D3.js Responsivo (Blue Theme)."""
        # noqa: E501
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comment Density Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            margin: 0; padding: 20px;
            background-color: #f4f4f4;
            display: flex; justify-content: center;
        }}
        .chart-container {{
            /* CORREÇÃO RESPONSIVA */
            width: 100%;
            max-width: 1066px;
            aspect-ratio: 1066 / 628;
            background: white; border: 1px solid #ccc;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            box-sizing: border-box;
        }}
    </style>
</head>
<body>

<div id="app" class="chart-container"></div>

<script>
    const data = {data_json};
    const width = 1066; const height = 628;
    const minThreshold = data.thresholds ? data.thresholds.min : "10%";
    const maxThreshold = data.thresholds ? data.thresholds.max : "50%";
    
    // CORREÇÃO: viewBox para escalar o SVG automaticamente
    const svg = d3.select("#app").append("svg")
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "100%")
        .style("background-color", "#fff");

    // HEADER (Azul)
    svg.append("rect").attr("x", 0).attr("y", 0).attr("width", width).attr("height", 70).attr("fill", "#0d6efd");
    svg.append("text").attr("x", 20).attr("y", 45).attr("fill", "white").style("font-size", "24px").style("font-weight", "bold").text("Comment Density Analysis");

    // Métricas Header
    const mGroup = svg.append("g").attr("transform", "translate(750, 20)");
    mGroup.append("rect").attr("x", 0).attr("width", 140).attr("height", 30).attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text").attr("x", 70).attr("y", 20).attr("text-anchor", "middle").attr("fill", "white").style("font-weight", "bold").text(`Files w/ Issues: ${{data.metrics.total_files}}`);
    
    mGroup.append("rect").attr("x", 150).attr("width", 140).attr("height", 30).attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text").attr("x", 220).attr("y", 20).attr("text-anchor", "middle").attr("fill", "white").style("font-weight", "bold").text(`Total Violations: ${{data.metrics.total_issues}}`);

    const col1X = 50; const col2X = 550; const contentY = 120;

    // --------------------------------------------------------
    // CHART 1: REFERENCE (Glossário)
    // --------------------------------------------------------
    svg.append("text").attr("x", col1X).attr("y", contentY - 10).style("font-size", "18px").style("font-weight", "bold").text("Reference: What are these?");
    const defGroup = svg.append("g").attr("transform", `translate(${{col1X}}, ${{contentY}})`);
    
    const definitions = [
        {{ code: "LOW_COMMENT_DENSITY", color: "#fd7e14", title: "Low Density", desc: `Less than ${{minThreshold}} of comments. Hard to maintain.` }},
        {{ code: "HIGH_COMMENT_DENSITY", color: "#dc3545", title: "High Density", desc: `More than ${{maxThreshold}} of comments. Code might be cluttered.` }}
    ];

    definitions.forEach((def, i) => {{
        const yPos = i * 80;
        defGroup.append("rect").attr("x", 0).attr("y", yPos).attr("width", 450).attr("height", 70).attr("rx", 5).attr("fill", "#f8f9fa").attr("stroke", "#eee");
        defGroup.append("rect").attr("x", 0).attr("y", yPos).attr("width", 5).attr("height", 70).attr("fill", def.color);
        defGroup.append("text").attr("x", 15).attr("y", yPos + 25).style("font-weight", "bold").style("font-size", "14px").attr("fill", "#333").text(def.title + " (" + def.code + ")");
        defGroup.append("text").attr("x", 15).attr("y", yPos + 50).style("font-size", "13px").attr("fill", "#666").text(def.desc);
    }});

    // --------------------------------------------------------
    // CHART 2: RULES (Counts)
    // --------------------------------------------------------
    const rulesY = contentY + 200 + 40;
    svg.append("text").attr("x", col1X).attr("y", rulesY - 10).style("font-size", "18px").style("font-weight", "bold").text("Violation Counts");
    
    const textPadding = 160; 
    const ruleGroup = svg.append("g").attr("transform", `translate(${{col1X + textPadding}}, ${{rulesY}})`);
    const ruleData = (data.rule_counts || []).slice(0, 5);
    
    if(ruleData.length > 0) {{
        const maxCount = d3.max(ruleData, d => d.count);
        const xRule = d3.scaleLinear().domain([0, maxCount * 1.2]).range([0, 450 - textPadding]);
        const yRule = d3.scaleBand().domain(ruleData.map(d => d.code)).range([0, 150]).padding(0.2);
        
        ruleGroup.append("g").call(d3.axisLeft(yRule));
        ruleGroup.selectAll("rect").data(ruleData).enter().append("rect")
            .attr("x", 1).attr("y", d => yRule(d.code)).attr("width", d => xRule(d.count))
            .attr("height", yRule.bandwidth()).attr("fill", "#0d6efd");
            
        ruleGroup.selectAll("text.val").data(ruleData).enter().append("text")
            .attr("x", d => xRule(d.count) + 5).attr("y", d => yRule(d.code) + yRule.bandwidth()/2 + 4)
            .style("font-size", "11px").style("font-weight", "bold").text(d => d.count);
    }} else {{
        svg.append("text").attr("x", col1X).attr("y", rulesY + 50).text("No violations found.");
    }}

    // --------------------------------------------------------
    // LIST: TOP OFFENDERS (COM INDICADOR COLORIDO)
    // --------------------------------------------------------
    svg.append("text").attr("x", col2X).attr("y", contentY - 10).style("font-size", "18px").style("font-weight", "bold").text("Files with Most Violations");
    const listGroup = svg.append("g").attr("transform", `translate(${{col2X}}, ${{contentY}})`);
    listGroup.append("rect").attr("width", 450).attr("height", 420).attr("fill", "#fafafa").attr("stroke", "#eee");

    const offenders = data.top_files || [];
    const colorMap = {{ "LOW_COMMENT_DENSITY": "#fd7e14", "HIGH_COMMENT_DENSITY": "#dc3545" }};
    const labelMap = {{ "LOW_COMMENT_DENSITY": "LOW", "HIGH_COMMENT_DENSITY": "HIGH" }};

    if (offenders.length > 0) {{
        offenders.forEach((file, i) => {{
            const yPos = 30 + (i * 40);
            if (i > 0) listGroup.append("line").attr("x1", 10).attr("y1", yPos - 25).attr("x2", 440).attr("y2", yPos - 25).attr("stroke", "#eee");
            
            let fileName = file.file;
            if (fileName.length > 40) fileName = "..." + fileName.slice(-37);
            
            // 1. Nome do Ficheiro
            listGroup.append("text").attr("x", 15).attr("y", yPos).style("font-family", "monospace").style("font-size", "12px").text(`${{i+1}}. ${{fileName}}`);
            
            // 2. Indicador Colorido (O "Violation Reference")
            const vType = file.type || "UNKNOWN";
            const vColor = colorMap[vType] || "#999";
            const vLabel = labelMap[vType] || "?";
            
            // Caixa do indicador
            listGroup.append("rect").attr("x", 330).attr("y", yPos - 12).attr("width", 45).attr("height", 18).attr("rx", 3).attr("fill", vColor);
            // Texto do indicador
            listGroup.append("text").attr("x", 352).attr("y", yPos + 1).attr("text-anchor", "middle").attr("fill", "white").style("font-size", "10px").style("font-weight", "bold").text(vLabel);

            // 3. Contador Total (Badge Cinza)
            listGroup.append("rect").attr("x", 400).attr("y", yPos - 12).attr("width", 30).attr("height", 18).attr("rx", 4).attr("fill", "#6c757d");
            listGroup.append("text").attr("x", 415).attr("y", yPos + 1).attr("text-anchor", "middle").attr("fill", "white").style("font-size", "11px").style("font-weight", "bold").text(file.count);
        }});
    }} else {{
        if (data.metrics.total_issues > 0) {{
             listGroup.append("text").attr("x", 225).attr("y", 210).attr("text-anchor", "middle").attr("fill", "#dc3545").text("⚠️ Issues found (Files unavailable)");
        }} else {{
             listGroup.append("text").attr("x", 225).attr("y", 210).attr("text-anchor", "middle").attr("fill", "#28a745").style("font-size", "16px").text("✅ Code looks clean!");
        }}
    }}
</script>
</body>
</html>"""  # noqa: E501
