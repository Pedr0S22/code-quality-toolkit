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

    def generate_dashboard(self, results, output_dir=None):
        # 1. Determine Output Directory & Filename
        if output_dir is None:
            output_dir = Path(__file__).parent

        # Dynamic naming: 'linter_wrapper' -> 'Linter Wrapper'
        current_folder_name = Path(__file__).parent.name 
        
        # Create a "Pretty" Title for the UI
        pretty_name = current_folder_name.replace("_", " ").title()
        
        filename = f"{current_folder_name}_dashboard.html"
        dashboard_file = Path(output_dir) / filename

        # 2. Unpack Data
        if isinstance(results, dict):
            raw_issues = results.get("results", [])
        else:
            raw_issues = results

        # 3. Normalize Paths (Windows/Linux compatibility)
        clean_issues = []
        for issue in raw_issues:
            new_issue = issue.copy()
            raw_path = new_issue.get("file", "unknown")
            norm_path = raw_path.replace("\\", "/")

            if "/source/" in norm_path:
                parts = norm_path.split("/source/")
                if len(parts) > 1:
                    relative_part = parts[-1]
                    clean_rel = relative_part.replace("/", "\\")
                    new_issue["file"] = f".\\{clean_rel}"
            
            clean_issues.append(new_issue)

        all_issues = clean_issues

        # 4. Aggregation Logic
        total_issues = len(all_issues)
        
        files_map = {}
        for issue in all_issues:
            f_path = issue.get("file", "unknown")
            files_map[f_path] = files_map.get(f_path, 0) + 1
        
        unique_files_list = sorted(list(files_map.keys()))

        severity_counts_map = {}
        for issue in all_issues:
            sev = issue.get("severity", "low")
            severity_counts_map[sev] = severity_counts_map.get(sev, 0) + 1

        # 5. JSON Payload
        dashboard_data = {
            "results": all_issues,
            "metrics": {
                "total_issues": total_issues,
                "total_files": len(unique_files_list),
                "unique_files": unique_files_list,
                "severity_counts": severity_counts_map,
            },
        }

        data_json = json.dumps(dashboard_data)

        # 6. HTML Template (Now with {{PLUGIN_NAME}} placeholders)
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{{PLUGIN_NAME}} Dashboard</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #1e1e1e;
        color: #333;
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: 1fr;
        grid-template-rows: auto 1fr;
        gap: 20px;
        max-width: 100%;
        height: 90vh;
    }

    .dashboard-title {
        font-size: 24px;
        font-weight: 600;
        color: #007ACC;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }

    /* METRICS (Top Row) */
    .metrics-container {
        display: flex;
        gap: 20px;
        margin-bottom: 10px;
        height: 280px; 
    }
    .card {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
    }

    .metric-card {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    .metric-value {
        font-size: 48px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 5px;
        font-weight: 600;
    }

    /* Severity Badges */
    .sev-badge-group {
        display: flex;
        flex-direction: column;
        gap: 15px;
        width: 100%;
        padding: 0 20px;
    }
    .sev-badge {
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        color: white;
        display: flex;
        justify-content: space-between;
    }
    .bg-high { background-color: #dc3545; }
    .bg-medium { background-color: #ffc107; color: #333; }
    .bg-low { background-color: #0d6efd; }

    /* Chart Container */
    .chart-container {
        flex: 2;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* TABLE LAYOUT */
    .main-content {
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .table-wrapper {
        flex: 1;
        overflow: auto;
        border: 1px solid #eee;
        border-radius: 4px;
        position: relative;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        table-layout: fixed;
        min-width: 1000px;
    }

    thead {
        position: sticky;
        top: 0;
        z-index: 20;
    }

    th {
        background: #fafafa;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #ddd;
        color: #555;
        user-select: none;
        position: relative;
        box-shadow: 0 1px 0 #ddd;
    }

    th:hover { background-color: #eee; }

    td {
        padding: 10px 12px;
        border-bottom: 1px solid #f0f0f0;
        color: #333;
        vertical-align: top;
    }

    td.no-wrap {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    td.msg-col {
        white-space: normal;
        word-break: break-word;
        cursor: text;
        user-select: text;
    }

    tr:hover { background-color: #f8f9fa; }

    .sort-icon {
        font-size: 10px;
        margin-left: 5px;
        color: #bbb;
        cursor: pointer;
    }
    th.active .sort-icon { color: #333; }

    .resizer {
        position: absolute;
        top: 0;
        right: 0;
        width: 5px;
        cursor: col-resize;
        user-select: none;
        height: 100%;
        background: transparent;
        z-index: 30;
    }
    .resizer:hover, .resizing { background: #0d6efd; }
</style>
</head>
<body>

<div class="dashboard-grid">
    <div class="dashboard-title">{{PLUGIN_NAME}} Dashboard</div>

    <div class="metrics-container">
        
        <div class="card metric-card" style="flex: 0.8;">
            <div class="metric-value" id="total-issues">0</div>
            <div class="metric-label">Total Issues</div>
        </div>

        <div class="card metric-card" style="flex: 1;">
            <h4 style="margin: 0 0 15px 0; color: #555; font-size: 14px;">Breakdown</h4>
            <div class="sev-badge-group">
                <div class="sev-badge bg-high">
                    <span>HIGH</span> <span id="count-high">0</span>
                </div>
                <div class="sev-badge bg-medium">
                    <span>MED</span> <span id="count-medium">0</span>
                </div>
                <div class="sev-badge bg-low">
                    <span>LOW</span> <span id="count-low">0</span>
                </div>
            </div>
        </div>

        <div class="card chart-container">
            <h4 style="margin: 0 0 5px 0; color: #555
            ; font-size: 14px;">Severity Distribution</h4>
            <div id="chart-area" style="width: 100%; height: 100%;"></div>
        </div>
    </div>

    <div class="main-content card" style="padding: 0;">
        <div class="table-wrapper">
            <table id="issues-table">
                <thead>
                    <tr>
                        <th style="width: 90px;" onclick="handleSort('severity')">
                            Severity <span class="sort-icon">↕</span>
                            <div class="resizer"></div>
                        </th>
                        <th style="width: 250px;" onclick="handleSort('file')">
                            File <span class="sort-icon">↕</span>
                            <div class="resizer"></div>
                        </th>
                        <th style="width: 100px;" onclick="handleSort('code')">
                            Code <span class="sort-icon">↕</span>
                            <div class="resizer"></div>
                        </th>
                        <th style="width: 70px;" onclick="handleSort('line')">
                            Line <span class="sort-icon">↕</span>
                            <div class="resizer"></div>
                        </th>
                        <th style="width: auto;" onclick="handleSort('message')">
                            Message <span class="sort-icon">↕</span>
                            <div class="resizer"></div>
                        </th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
</div>

<script>
    let issues = [];
    let currentSort = { column: 'severity', direction: 'desc' };
    const severityWeight = {
        "fatal": 4, "high": 3, "medium": 2,
        "low": 1, "convention": 1, "refactor": 1
    };

    try {
        const rawData = {{DATA_JSON}} || {};
        
        if (Array.isArray(rawData)) { issues = rawData; } 
        else { issues = rawData.results || []; }

        const metrics = rawData.metrics || {};
        
        document.getElementById('total-issues').textContent =
            metrics.total_issues || issues.length;
        
        const sevCounts = metrics.severity_counts || {};
        ['high', 'medium', 'low'].forEach(k => {
             document.getElementById(`count-${k}`).textContent = sevCounts[k] || 0;
        });

        if (typeof d3 !== 'undefined') {
            const chartData = ["high", "medium", "low"].map(k => ({
                label: k.toUpperCase(),
                key: k,
                value: sevCounts[k] || 0
            }));
            const container = document.getElementById("chart-area");
            const width = container.clientWidth || 400;
            const height = container.clientHeight || 200;
            const margin = {top: 20, right: 30, bottom: 30, left: 40};

            container.innerHTML = '';
            const svg = d3.select("#chart-area").append("svg")
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("viewBox", `0 0 ${width} ${height}`)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);

            const colors = {
                "high": "#dc3545", "medium": "#ffc107", "low": "#0d6efd"
            };

            const x = d3.scaleBand()
                .range([0, width - margin.left - margin.right])
                .domain(chartData.map(d => d.label))
                .padding(0.4);

            const yMax = d3.max(chartData, d => d.value) || 10;
            const y = d3.scaleLinear()
                .domain([0, yMax])
                .range([height - margin.top - margin.bottom, 0]);

            svg.append("g")
                .attr("transform",
                `translate(0, ${height - margin.top - margin.bottom})`)
                .call(d3.axisBottom(x).tickSize(0))
                .selectAll("text").style("font-size", "11px")
                .style("font-weight", "bold");

            svg.append("g").call(d3.axisLeft(y).ticks(5));

            svg.selectAll("bars").data(chartData).join("rect")
                .attr("x", d => x(d.label))
                .attr("y", d => y(d.value))
                .attr("width", x.bandwidth())
                .attr("height", d => (height - margin.top - margin.bottom) - y(d.value))
                .attr("fill", d => colors[d.key]);
        }

        // Resizer & Sorting Logic (Same as before)
        document.querySelectorAll('.resizer').forEach(resizer => {
            let x = 0; let w = 0; let th = null;
            const mouseDownHandler = function(e) {
                e.stopPropagation(); th = resizer.parentElement;
                x = e.clientX; w = th.offsetWidth;
                resizer.classList.add('resizing');
                document.addEventListener('mousemove', mouseMoveHandler);
                document.addEventListener('mouseup', mouseUpHandler);
            };
            const mouseMoveHandler = function(e) {
                const dx = e.clientX - x; th.style.width = `${w + dx}px`;
            };
            const mouseUpHandler = function() {
                resizer.classList.remove('resizing');
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
            };
            resizer.addEventListener('mousedown', mouseDownHandler);
        });

        window.handleSort = function(column) {
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' 
                ? 'desc' : 'asc';
            } else {
                currentSort.column = column; currentSort.direction = 'asc';
            }
            issues.sort((a, b) => {
                let valA = a[column], valB = b[column];
                if (column === 'severity') {
                    valA = severityWeight[(valA || '').toLowerCase()] || 0;
                    valB = severityWeight[(valB || '').toLowerCase()] || 0;
                } else if (column === 'line') {
                    valA = parseInt(valA) || 0; valB = parseInt(valB) || 0;
                } else {
                    valA = (valA || '').toString().toLowerCase();
                    valB = (valB || '').toString().toLowerCase();
                }
                if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
                if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
                return 0;
            });
            updateSortIcons(); renderTable();
        };

        function updateSortIcons() {
            document.querySelectorAll('.sort-icon')
            .forEach(icon => icon.textContent = '↕');
            const activeHeader = document.querySelector(
            `th[onclick="handleSort('${currentSort.column}')"]`);
            if (activeHeader) {
                activeHeader.querySelector('.sort-icon').textContent =
                    currentSort.direction === 'asc' ? '▲' : '▼';
            }
        }

        function renderTable() {
            const tbody = document.querySelector("#issues-table tbody");
            tbody.innerHTML = '';
            if (!issues.length) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;\
                  padding:20px;">No issues found.</td></tr>';
                return;
            }
            issues.forEach(issue => {
                const tr = document.createElement("tr");
                const sev = (issue.severity || 'low').toLowerCase();
                const sevClass = sev === 'fatal' ? 'high' : sev;
                const sevColor = sevClass === 'high' ?
                  '#dc3545' : sevClass === 'medium' ? '#ffc107' : '#0d6efd';

                tr.innerHTML = `
                    <td class="no-wrap" style="font-weight:bold; color: ${sevColor}">
                        ${sev.toUpperCase()}
                    </td>
                    <td class="no-wrap" title="${issue.file || 'unknown'}">
                        ${issue.file || 'unknown'}
                    </td>
                    <td class="no-wrap"><span class="top-issue-code">${issue.code || ''}
                    </span></td>
                    <td class="no-wrap">${issue.line || ''}</td>
                    <td class="msg-col">${issue.message || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        handleSort('severity');

    } catch (e) {
        console.error(e);
        document.body.innerHTML = `<h3 style="color:red">
        Error rendering dashboard: ${e.message}</h3>`;
    }
</script>
</body>
</html>
"""
        # 7. Perform Replacements
        final_html = html.replace("{{DATA_JSON}}", data_json)
        final_html = final_html.replace("{{PLUGIN_NAME}}", pretty_name)

        dashboard_file.write_text(final_html, encoding="utf-8")
        
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
