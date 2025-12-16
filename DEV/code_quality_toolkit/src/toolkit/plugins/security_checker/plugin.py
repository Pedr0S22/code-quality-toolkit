from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# Imports do Bandit
try:
    from bandit.core.config import BanditConfig
    from bandit.core.constants import HIGH, LOW, MEDIUM
    from bandit.core.manager import BanditManager

except ImportError:
    BanditConfig = None
    BanditManager = None
    LOW, MEDIUM, HIGH = None, None, None

# Imports do Core
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class Plugin:
    """
    Plugin de Segurança: Um "wrapper" que executa o Bandit.
    Gera Dashboard D3.js Responsivo (Tema Vermelho).
    """

    def __init__(self) -> None:
        if BanditManager is None:
            # ERRO: Falha se o Bandit não estiver instalado, sem fallback.
            raise ImportError(
                "O plugin SecurityChecker requer o 'bandit'. "
                "Instale-o via 'pip install bandit'."
            )

        self.report_severity_level = "LOW"

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "SecurityChecker",
            "version": "1.1.0",
            "description": "Deteta vulnerabilidades (eval, SQLi, etc.) com Bandit.",
        }

    def configure(self, config: ToolkitConfig) -> None:
        if hasattr(config.rules, "security_report_level"):
            self.report_severity_level = config.rules.security_report_level

    # O MÉTODO _run_fallback_scan FOI REMOVIDO PERMANENTEMENTE

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Executa a análise de segurança usando apenas o Bandit."""
        results: list[IssueResult] = []
        temp_file_path: str = ""

        try:
            # --- Scanner Principal (Bandit) ---
            with tempfile.NamedTemporaryFile(
                suffix=".py", delete=False, mode="w", encoding="utf-8"
            ) as temp_file:
                temp_file.write(source_code)
                temp_file_path = temp_file.name

            config = BanditConfig()
            manager = BanditManager(config=config, agg_type="vuln")
            manager.discover_files([temp_file_path])
            manager.run_tests()

            severity_map = {"LOW": LOW, "MEDIUM": MEDIUM, "HIGH": HIGH}
            report_level = severity_map.get(self.report_severity_level, LOW)

            bandit_issues = manager.get_issue_list(
                sev_level=report_level, conf_level=LOW
            )

            for issue in bandit_issues:
                sev_trans = {
                    "LOW": "low",
                    "MEDIUM": "medium",
                    "HIGH": "high",
                }
                results.append(
                    {
                        "severity": sev_trans.get(issue.severity, "low"),
                        "code": issue.test_id,
                        "message": issue.text,
                        "line": issue.lineno,
                        "col": issue.col_offset + 1,
                        "hint": f"Bandit ID: {issue.test_id}",
                    }
                )

        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Erro SecurityChecker: {str(e)}",
                },
            }

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # Lógica de retorno de sucesso
        filename_to_save = str(file_path) if file_path else "unknown"
        for r in results:
            r["file"] = filename_to_save

        return {
            "results": results,
            "summary": {"issues_found": len(results), "status": "completed"},
        }

    # ==========================================================================
    # DASHBOARD GENERATION
    # ==========================================================================

    def generate_dashboard(
        self,
        aggregated_results: list[dict],
        output_path: str = "security_checker_dashboard.html",
        dependency_data: dict = None,
    ) -> str:
        """Gera o dashboard D3.js."""

        # 1. Agregação Robusta
        dashboard_data = self._aggregate_data_for_dashboard(aggregated_results)

        # print(
        #     f"[SecurityChecker] Dashboard: "
        #     f"{dashboard_data['metrics']['total_issues']} vulnerabilidades."
        # )

        # 2. Geração do HTML
        data_json = json.dumps(dashboard_data)
        html_content = self._get_html_template(data_json)

        # 3. Salvamento
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
            # print(f"[SecurityChecker] Erro ao salvar dashboard: {e}")
            return ""

    def _aggregate_data_for_dashboard(self, results: list[dict]) -> dict:
        """
        Normaliza os dados para o D3.js.
        """
        flattened_issues = []

        # Normalização: Extrair todos os issues
        for entry in results:
            if "plugins" in entry:
                file_path = entry.get("file", "unknown")
                plugins_list = entry.get("plugins", [])

                plugin_res = next(
                    (p for p in plugins_list if p["plugin"] == "SecurityChecker"), None
                )
                if plugin_res:
                    issues = plugin_res.get("results", [])
                    for issue in issues:
                        if "file" not in issue:
                            issue["file"] = file_path
                        flattened_issues.append(issue)

            elif "code" in entry or "severity" in entry:
                # Caso venha flat (compatibilidade)
                flattened_issues.append(entry)

        # Contagem
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        rule_counts = {}
        files_counter = {}

        for issue in flattened_issues:
            # Pega a severidade, padronizando para 'info' se a chave estiver ausente
            sev = issue.get("severity", "info").lower()

            # CORREÇÃO: Se a severidade lida não for uma das chaves válidas, use 'info'.
            if sev not in severity_counts:
                sev = "info"

            severity_counts[sev] += 1

            code = issue.get("code", "UNKNOWN")
            rule_counts[code] = rule_counts.get(code, 0) + 1

            fname = issue.get("file", "unknown")
            files_counter[fname] = files_counter.get(fname, 0) + 1

        sev_data = [
            {"severity": k, "count": v} for k, v in severity_counts.items() if v > 0
        ]
        rule_data = [{"code": k, "count": v} for k, v in rule_counts.items()]
        rule_data.sort(key=lambda x: x["count"], reverse=True)

        top_files = [{"file": k, "count": v} for k, v in files_counter.items()]
        top_files.sort(key=lambda x: x["count"], reverse=True)

        return {
            "metrics": {
                "total_files": len(files_counter),
                "total_issues": len(flattened_issues),
            },
            "severity_counts": sev_data,
            "rule_counts": rule_data,
            "top_files": top_files[:10],
        }

    def _get_html_template(self, data_json: str) -> str:
        """Template D3.js Responsivo (Red Theme)."""
        # noqa: E501
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SecurityChecker Dashboard</title>
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

    // CORREÇÃO: viewBox para escalar o SVG automaticamente
    const svg = d3.select("#app").append("svg")
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "100%")
        .style("background-color", "#fff");

    // HEADER
    svg.append("rect")
        .attr("x", 0).attr("y", 0)
        .attr("width", width).attr("height", 70)
        .attr("fill", "#dc3545");

    svg.append("text")
        .attr("x", 20).attr("y", 45)
        .attr("fill", "white")
        .style("font-size", "24px").style("font-weight", "bold")
        .text("SecurityChecker Analysis");

    // METRICS
    const mGroup = svg.append("g").attr("transform", "translate(750, 20)");
    mGroup.append("rect")
        .attr("x", 0).attr("width", 140).attr("height", 30).attr("rx", 5)
        .attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text")
        .attr("x", 70).attr("y", 20).attr("text-anchor", "middle")
        .attr("fill", "white").style("font-weight", "bold")
        .text(`Files: ${{data.metrics.total_files}}`);

    mGroup.append("rect")
        .attr("x", 150).attr("width", 140).attr("height", 30).attr("rx", 5)
        .attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text")
        .attr("x", 220).attr("y", 20).attr("text-anchor", "middle")
        .attr("fill", "white").style("font-weight", "bold")
        .text(`Issues: ${{data.metrics.total_issues}}`);

    const col1X = 50; const col2X = 550; const contentY = 120;

    // CHART 1: SEVERITY
    svg.append("text")
        .attr("x", col1X).attr("y", contentY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Issues by Severity");

    const sevWidth = 450; const sevHeight = 200;
    const sevGroup = svg.append("g")
        .attr("transform", `translate(${{col1X}}, ${{contentY}})`);

    const sevData = data.severity_counts || [];
    if (sevData.length > 0) {{
        const xSev = d3.scaleBand()
            .domain(sevData.map(d => d.severity))
            .range([0, sevWidth]).padding(0.3);

        const maxVal = d3.max(sevData, d => d.count);
        const ySev = d3.scaleLinear()
            .domain([0, maxVal * 1.2]).range([sevHeight, 0]);

        sevGroup.append("g")
            .attr("transform", `translate(0,${{sevHeight}})`).call(d3.axisBottom(xSev));
        sevGroup.append("g").call(d3.axisLeft(ySev).ticks(5));

        const colorMap = {{
            "high": "#dc3545", "medium": "#ffc107",
            "low": "#17a2b8", "info": "#6c757d"
        }};

        sevGroup.selectAll("rect").data(sevData).enter().append("rect")
            .attr("x", d => xSev(d.severity))
            .attr("y", d => ySev(d.count))
            .attr("width", xSev.bandwidth())
            .attr("height", d => sevHeight - ySev(d.count))
            .attr("fill", d => colorMap[d.severity] || "steelblue");

        sevGroup.selectAll(".label").data(sevData).enter().append("text")
            .attr("x", d => xSev(d.severity) + xSev.bandwidth()/2)
            .attr("y", d => ySev(d.count) - 5)
            .attr("text-anchor", "middle")
            .style("font-size", "12px").style("font-weight", "bold")
            .text(d => d.count);
    }} else {{
         sevGroup.append("text").attr("y", 100).text("No data available");
    }}

    // CHART 2: RULES
    const rulesY = contentY + sevHeight + 60;
    svg.append("text")
        .attr("x", col1X).attr("y", rulesY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Top Vulnerabilities");

    const ruleGroup = svg.append("g")
        .attr("transform", `translate(${{col1X}}, ${{rulesY}})`);
    const ruleData = (data.rule_counts || []).slice(0, 5);

    if(ruleData.length > 0) {{
        const maxCount = d3.max(ruleData, d => d.count);
        const xRule = d3.scaleLinear()
            .domain([0, maxCount * 1.2]).range([0, sevWidth - 50]);
        const yRule = d3.scaleBand()
            .domain(ruleData.map(d => d.code)).range([0, 150]).padding(0.2);

        ruleGroup.append("g").call(d3.axisLeft(yRule));
        ruleGroup.selectAll("rect").data(ruleData).enter().append("rect")
            .attr("x", 1).attr("y", d => yRule(d.code))
            .attr("width", d => xRule(d.count))
            .attr("height", yRule.bandwidth()).attr("fill", "#6610f2");

        ruleGroup.selectAll("text.val").data(ruleData).enter().append("text")
            .attr("x", d => xRule(d.count) + 5)
            .attr("y", d => yRule(d.code) + yRule.bandwidth()/2 + 4)
            .style("font-size", "11px").style("font-weight", "bold")
            .text(d => d.count);
    }} else {{
        ruleGroup.append("text").attr("y", 50).text("No data available");
    }}

    // LIST: TOP OFFENDERS
    svg.append("text")
        .attr("x", col2X).attr("y", contentY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Top Risky Files");

    const listGroup = svg.append("g")
        .attr("transform", `translate(${{col2X}}, ${{contentY}})`);
    listGroup.append("rect")
        .attr("width", 450).attr("height", 420)
        .attr("fill", "#fafafa").attr("stroke", "#eee");

    const offenders = data.top_files || [];

    if (offenders.length > 0) {{
        offenders.forEach((file, i) => {{
            const yPos = 30 + (i * 40);
            if (i > 0) listGroup.append("line")
                .attr("x1", 10).attr("y1", yPos - 25)
                .attr("x2", 440).attr("y2", yPos - 25).attr("stroke", "#eee");

            let fileName = file.file;
            if (fileName.length > 50) fileName = "..." + fileName.slice(-47);

            listGroup.append("text")
                .attr("x", 15).attr("y", yPos)
                .style("font-family", "monospace").style("font-size", "12px")
                .text(`${{i+1}}. ${{fileName}}`);

            listGroup.append("rect")
                .attr("x", 400).attr("y", yPos - 12)
                .attr("width", 30).attr("height", 18).attr("rx", 4)
                .attr("fill", "#dc3545");

            listGroup.append("text")
                .attr("x", 415).attr("y", yPos + 1).attr("text-anchor", "middle")
                .attr("fill", "white").style("font-size", "11px")
                .style("font-weight", "bold").text(file.count);
        }});
    }} else {{
        if (data.metrics.total_issues > 0) {{
             listGroup.append("text")
                .attr("x", 225).attr("y", 210).attr("text-anchor", "middle")
                .attr("fill", "#dc3545").text("⚠️ Issues found (Files unavailable)");
        }} else {{
             listGroup.append("text")
                .attr("x", 225).attr("y", 210).attr("text-anchor", "middle")
                .attr("fill", "#28a745").style("font-size", "16px")
                .text("✅ No vulnerabilities found!");
        }}
    }}
</script>
</body>
</html>"""  # noqa: E501
