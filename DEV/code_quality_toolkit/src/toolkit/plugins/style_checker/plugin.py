"""Simple style checking plugin."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult

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

    def configure(self, config):
        # Compatibilidad con test antiguos que usan MockToolkitConfig
        if not hasattr(config, "plugins") or not hasattr(
            config.plugins, "style_checker"
        ):
            self.max_line_length = config.rules.max_line_length
            self.check_whitespace = config.rules.check_whitespace
            self.indent_style = config.rules.indent_style
            self.indent_size = config.rules.indent_size
            self.allow_mixed_indentation = config.rules.allow_mixed_indentation
            self.check_naming = config.rules.check_naming
            return

        # Configuración nueva vía [plugins.style_checker]
        sc = config.plugins.style_checker
        self.max_line_length = sc.max_line_length
        self.check_whitespace = sc.check_whitespace
        self.indent_style = sc.indent_style
        self.indent_size = sc.indent_size
        self.allow_mixed_indentation = sc.allow_mixed_indentation
        self.check_naming = sc.check_naming

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "StyleChecker",
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