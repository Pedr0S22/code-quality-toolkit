"""Lint wrapper plugin using pylint."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

_PYLINT_TYPE_TO_SEVERITY = {
    "convention": "low",
    "refactor": "low",
    "warning": "medium",
    "error": "high",
    "fatal": "high",
}


class Plugin:
    """Plugin que envuelve linters externos (inicialmente pylint)."""

    def __init__(self) -> None:
        self.enabled: bool = True
        self.linters: list[str] = ["pylint"]
        self.timeout_seconds: int = 60
        self.max_issues: int = 500
        self.pylint_args: list[str] = []
        self.fail_on_severity: str = "high"

    def configure(self, config: ToolkitConfig) -> None:
        """Configure o plugin a partir do ToolkitConfig."""
        lw = getattr(config, "linter_wrapper", None)

        if lw is not None:
            self.enabled = getattr(lw, "enabled", self.enabled)
            self.linters = list(getattr(lw, "linters", self.linters))
            self.timeout_seconds = int(
                getattr(lw, "timeout_seconds", self.timeout_seconds)
            )
            self.max_issues = int(getattr(lw, "max_issues", self.max_issues))
            self.pylint_args = list(getattr(lw, "pylint_args", self.pylint_args))
            self.fail_on_severity = str(
                getattr(lw, "fail_on_severity", self.fail_on_severity)
            )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "LinterWrapper",
            "version": "0.1.0",
            "description": (
                "Executa linters externos (como pylint) e normaliza os resultados "
                "para o relatório do toolkit."
            ),
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Analisa um único ficheiro com os linters configurados."""
        try:
            if not self.enabled:
                return {
                    "results": [],
                    "summary": {
                        "issues_found": 0,
                        "status": "completed",
                        "highest_severity": None,
                        "issues_by_severity": {},
                        "fail_build": False,
                    },
                }

            temp_path: str | None = None
            if file_path:
                target_path = file_path
            else:
                fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
                os.close(fd)
                with open(temp_path, "w", encoding="utf-8") as tmp:
                    tmp.write(source_code)
                target_path = temp_path

            try:
                results, highest_severity = self._run_linters_on_file(target_path)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

            issues_by_severity: dict[str, int] = {}
            for issue in results:
                sev = issue.get("severity", "low")
                issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

            fail_build = self._should_fail_build(highest_severity)

            # --- NOTE ---
            # We REMOVED the self.generate_dashboard() call from here.
            # It must be called by the Engine after collecting ALL results
            # to calculate the correct number of affected files.

            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                    "highest_severity": highest_severity,
                    "issues_by_severity": issues_by_severity,
                    "fail_build": fail_build,
                },
            }

        except Exception as exc:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(exc),
                },
            }

    def _run_linters_on_file(
        self,
        file_path: str,
    ) -> tuple[list[IssueResult], str | None]:
        """Executa todos os linters configurados num único ficheiro."""
        all_results: list[IssueResult] = []
        highest_severity: str | None = None
        order = {"low": 0, "medium": 1, "high": 2}

        for linter in self.linters:
            if linter == "pylint":
                lint_results = self._run_pylint(file_path)
            else:
                lint_results = [
                    {
                        "severity": "medium",
                        "code": "LINTER_UNSUPPORTED",
                        "message": (
                            f"Linter '{linter}' não é suportado pelo LinterWrapper."
                        ),
                        "file": file_path,
                        "line": 1,
                        "col": 1,
                        "hint": (
                            "Remover o linter não suportado da configuração "
                            "ou implementar suporte."
                        ),
                    }
                ]

            all_results.extend(lint_results)

            for issue in lint_results:
                sev = issue.get("severity", "low")
                val = order.get(sev, -1)
                cur = order.get(highest_severity, -1) if highest_severity else -1
                if val > cur:
                    highest_severity = sev

            if len(all_results) >= self.max_issues:
                all_results = all_results[: self.max_issues]
                break

        return all_results, highest_severity

    def _run_pylint(self, file_path: str) -> list[IssueResult]:
        """Executa pylint no ficheiro dado e converte a saída JSON em IssueResult."""
        timeout_seconds = self.timeout_seconds
        extra_args = list(self.pylint_args)

        cmd: list[str] = [
            sys.executable,
            "-m",
            "pylint",
            "--output-format=json",
            *extra_args,
            file_path,
        ]

        try:
            proc = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_NOT_FOUND",
                    "message": "Python interpreter not found.",
                    "file": file_path,
                    "line": 1,
                    "col": 1,
                    "hint": "Check your python installation.",
                }
            ]
        except subprocess.TimeoutExpired:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_TIMEOUT",
                    "message": (
                        f"'pylint' não terminou dentro de {timeout_seconds} segundos."
                    ),
                    "file": file_path,
                    "line": 1,
                    "col": 1,
                    "hint": (
                        "Simplifique o ficheiro ou aumente o timeout "
                        "em [plugins.linter_wrapper]."
                    ),
                }
            ]

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if proc.returncode != 0 and "No module named" in stderr and "pylint" in stderr:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_NOT_FOUND",
                    "message": "O módulo 'pylint' não foi encontrado.",
                    "file": file_path,
                    "line": 1,
                    "col": 1,
                    "hint": "Instale pylint (pip install pylint).",
                }
            ]

        if not stdout:
            if proc.returncode != 0:
                return [
                    {
                        "severity": "high",
                        "code": "LINTER_ERROR",
                        "message": (
                            "pylint terminou com erro e não produziu saída JSON."
                        ),
                        "file": file_path,
                        "line": 1,
                        "col": 1,
                        "hint": f"Verifique stderr: {stderr or 'sem stderr'}.",
                    }
                ]
            return []

        try:
            messages = json.loads(stdout)
        except json.JSONDecodeError:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_OUTPUT_INVALID",
                    "message": "Saída do pylint não é JSON válido.",
                    "file": file_path,
                    "line": 1,
                    "col": 1,
                    "hint": "Verifique plugins/customizações do pylint.",
                }
            ]

        results: list[IssueResult] = []

        for msg in messages:
            msg_type = str(msg.get("type", "") or "")
            severity = _PYLINT_TYPE_TO_SEVERITY.get(msg_type, "low")

            line = int(msg.get("line", 0) or 0)
            col = int(msg.get("column", 0) or 0)
            msg_id = (
                str(msg.get("message-id", "")) or str(msg.get("symbol", "")) or "PYLINT"
            )
            text = str(msg.get("message", "")) or ""

            # --- FIX: CAPTURE FILENAME ---
            # We must explicitly capture the path here so the dashboard knows it.
            msg_file = str(msg.get("path", file_path))

            results.append(
                {
                    "severity": severity,
                    "code": msg_id,
                    "message": text,
                    "file": msg_file,  # Added Key
                    "line": line,
                    "col": col,
                    "hint": f"Reveja a regra '{msg_id}'.",
                }
            )

            if len(results) >= self.max_issues:
                break

        return results

    def _should_fail_build(self, highest_severity: str | None) -> bool:
        if not highest_severity:
            return False
        if self.fail_on_severity == "none":
            return False

        order = {"low": 0, "medium": 1, "high": 2}
        threshold = order.get(self.fail_on_severity, 2)
        max_seen = order.get(highest_severity, -1)
        return max_seen >= threshold

    def generate_dashboard(self, results, output_dir=None):
        if output_dir is None:
            output_dir = Path(__file__).parent

        filename = "linter_wrapper_dashboard.html"
        dashboard_file = Path(output_dir) / filename

        # 1. Unpack Data
        if isinstance(results, dict):
            raw_issues = results.get("results", [])
        else:
            raw_issues = results

        # 2. Normalize Paths
        clean_issues = []
        for issue in raw_issues:
            new_issue = issue.copy()
            raw_path = new_issue.get("file", "unknown")
            norm_path = raw_path.replace("\\", "/")

            if "/source/" in norm_path:
                parts = norm_path.split("/source/")
                if len(parts) > 1:
                    relative_part = parts[-1]
                    # Fix for Python < 3.12: Perform replace outside f-string
                    clean_rel = relative_part.replace("/", "\\")
                    new_issue["file"] = f".\\{clean_rel}"

            clean_issues.append(new_issue)

        all_issues = clean_issues

        # 3. Aggregation Logic
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

        # 4. JSON Payload
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

        # Refactored HTML string to satisfy line length limits (E501)
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>LinterWrapper Dashboard</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #f4f6f9;
        color: #333;
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: 280px 1fr;
        grid-template-rows: auto auto 1fr;
        gap: 20px;
        max-width: 1400px;
        margin: 0 auto;
        height: 90vh;
    }

    .dashboard-title {
        grid-column: 1 / -1;
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }

    /* METRICS */
    .metrics-container {
        grid-column: 1 / -1;
        display: flex;
        gap: 20px;
        margin-bottom: 10px;
    }
    .card {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
    }

    .metric-card {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 13px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 5px;
    }

    .sev-badge-group {
        display: flex;
        gap: 15px;
        margin-top: 10px;
    }
    .sev-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        color: white;
    }
    .bg-high { background-color: #dc3545; }
    .bg-medium { background-color: #ffc107; color: #333; }
    .bg-low { background-color: #0d6efd; }

    /* SIDEBAR */
    .sidebar {
        grid-column: 1 / 2;
        display: flex;
        flex-direction: column;
        gap: 20px;
        overflow-y: auto;
    }
    .file-list {
        font-size: 13px;
        color: #555;
        max-height: 150px;
        overflow-y: auto;
        width: 100%;
        border-top: 1px solid #eee;
        margin-top: 10px;
        padding-top: 10px;
    }
    .file-item {
        padding: 4px 0;
        border-bottom: 1px dashed #eee;
        display: flex;
        justify-content: space-between;
        word-break: break-all;
    }
    .top-issues-list { list-style: none; padding: 0; margin: 0; }
    .top-issue-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 13px;
    }
    .top-issue-code {
        font-family: monospace;
        font-weight: bold;
        background: #eee;
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* TABLE LAYOUT & SCROLLING */
    .main-content {
        grid-column: 2 / -1;
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
        min-width: 800px;
    }

    /* FIXED HEADER STYLES */
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

    /* MESSAGE COLUMN STYLES */
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

    /* RESIZER */
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
    <div class="dashboard-title">LinterWrapper Dashboard</div>

    <div class="metrics-container">
        <div class="card metric-card">
            <div class="metric-value" id="total-issues">0</div>
            <div class="metric-label">Total Issues</div>
        </div>
        <div class="card metric-card" style="flex: 1.5;">
            <div class="metric-value" id="total-files">0</div>
            <div class="metric-label">Files Affected</div>
            <div id="file-list-container" class="file-list"></div>
        </div>
        <div class="card metric-card" style="flex: 1.5;">
            <div class="sev-badge-group">
                <span class="sev-badge bg-high">
                    HIGH: <span id="count-high">0</span>
                </span>
                <span class="sev-badge bg-medium">
                    MED: <span id="count-medium">0</span>
                </span>
                <span class="sev-badge bg-low">
                    LOW: <span id="count-low">0</span>
                </span>
            </div>
            <div class="metric-label" style="margin-top: 15px;">
                Severity Breakdown
            </div>
        </div>
    </div>

    <div class="sidebar">
        <div class="card" style="height: 300px; display: flex;
             flex-direction: column; align-items: center;">
            <h4 style="margin: 0 0 10px 0; font-size: 14px;
                       color: #555;">Severity Distribution</h4>
            <div id="chart-area" style="flex: 1; width: 100%;"></div>
        </div>
        <div class="card" style="flex: 1;">
            <h4 style="margin: 0 0 15px 0; font-size: 14px;
                       color: #555;">Top Recurring Issues</h4>
            <ul id="top-issues" class="top-issues-list"></ul>
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
        document.getElementById('total-files').textContent =
            metrics.total_files || 0;
        
        const sevCounts = metrics.severity_counts || {};
        ['high', 'medium', 'low'].forEach(k => {
             document.getElementById(`count-${k}`).textContent = sevCounts[k] || 0;
        });

        const fileContainer = document.getElementById('file-list-container');
        const uniqueFiles = metrics.unique_files || [];
        if (uniqueFiles.length === 0) {
            fileContainer.innerHTML =
                '<div style="font-style:italic;">No files recorded</div>';
        } else {
            uniqueFiles.forEach(f => {
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `<span title="${f}">${f}</span>`;
                fileContainer.appendChild(div);
            });
        }

        const codeCounts = {};
        issues.forEach(i => {
            const code = i.code || 'UNKNOWN';
            codeCounts[code] = (codeCounts[code] || 0) + 1;
        });
        const sortedCodes = Object.entries(codeCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
            
        const topIssuesList = document.getElementById('top-issues');
        if (sortedCodes.length === 0) {
            topIssuesList.innerHTML =
                '<li style="color:#999; font-style:italic;">No issues found.</li>';
        } else {
            sortedCodes.forEach(([code, count]) => {
                const li = document.createElement('li');
                li.className = 'top-issue-item';
                li.innerHTML =
                    `<span class="top-issue-code">${code}</span> 
                    <span>${count}x</span>`;
                topIssuesList.appendChild(li);
            });
        }

        if (typeof d3 !== 'undefined') {
            const chartData = ["high", "medium", "low"].map(k => ({
                label: k.toUpperCase(),
                key: k,
                value: sevCounts[k] || 0
            }));
            const container = document.getElementById("chart-area");
            const width = container.clientWidth || 200;
            const height = 250;
            const margin = {top: 20, right: 20, bottom: 30, left: 40};
            container.innerHTML = '';
            const svg = d3.select("#chart-area").append("svg")
                .attr("width", width).attr("height", height)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);

            const colors = {
                "high": "#dc3545",
                "medium": "#ffc107",
                "low": "#0d6efd"
            };
            const x = d3.scaleBand()
                .range([0, width - margin.left - margin.right])
                .domain(chartData.map(d => d.label))
                .padding(0.4);
            const y = d3.scaleLinear()
                .domain([0, d3.max(chartData, d => d.value) + 2])
                .range([height - margin.top - margin.bottom, 0]);

            svg.append("g")
                .attr("transform", `translate(0,
                ${height - margin.top - margin.bottom})`)
                .call(d3.axisBottom(x).tickSize(0))
                .selectAll("text").style("font-size", "10px");
            svg.append("g").call(d3.axisLeft(y).ticks(5));
            svg.selectAll("bars").data(chartData).join("rect")
                .attr("x", d => x(d.label))
                .attr("y", d => y(d.value))
                .attr("width", x.bandwidth())
                .attr("height", d =>
                    (height - margin.top - margin.bottom) - y(d.value)
                )
                .attr("fill", d => colors[d.key]);
        }

        document.querySelectorAll('.resizer').forEach(resizer => {
            let x = 0;
            let w = 0;
            let th = null;
            const mouseDownHandler = function(e) {
                e.stopPropagation();
                th = resizer.parentElement;
                x = e.clientX;
                w = th.offsetWidth;
                resizer.classList.add('resizing');
                document.addEventListener('mousemove', mouseMoveHandler);
                document.addEventListener('mouseup', mouseUpHandler);
            };
            const mouseMoveHandler = function(e) {
                const dx = e.clientX - x;
                th.style.width = `${w + dx}px`;
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
                currentSort.direction =
                    currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'asc';
            }
            issues.sort((a, b) => {
                let valA = a[column], valB = b[column];
                if (column === 'severity') {
                    valA = severityWeight[(valA || '').toLowerCase()] || 0;
                    valB = severityWeight[(valB || '').toLowerCase()] || 0;
                } else if (column === 'line') {
                    valA = parseInt(valA) || 0;
                    valB = parseInt(valB) || 0;
                } else {
                    valA = (valA || '').toString().toLowerCase();
                    valB = (valB || '').toString().toLowerCase();
                }
                if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
                if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
                return 0;
            });
            updateSortIcons();
            renderTable();
        };

        function updateSortIcons() {
            document.querySelectorAll('.sort-icon').forEach(
                icon => icon.textContent = '↕'
            );
            const activeHeader = document.querySelector(
                `th[onclick="handleSort('${currentSort.column}')"]`
            );
            if (activeHeader) {
                activeHeader.querySelector('.sort-icon').textContent =
                    currentSort.direction === 'asc' ? '▲' : '▼';
            }
        }

        function renderTable() {
            const tbody = document.querySelector("#issues-table tbody");
            tbody.innerHTML = '';
            if (!issues.length) {
                tbody.innerHTML =
                    '<tr><td colspan="5" style="text-align:center; padding:20px;">' +
                    'No issues found.</td></tr>';
                return;
            }
            issues.forEach(issue => {
                const tr = document.createElement("tr");
                const sev = (issue.severity || 'low').toLowerCase();
                const sevClass = sev === 'fatal' ? 'high' : sev;
                
                const sevColor = sevClass === 'high' ? '#dc3545' :
                                 sevClass === 'medium' ? '#ffc107' : '#0d6efd';

                tr.innerHTML = `
                    <td class="no-wrap" style="font-weight:bold; color: ${sevColor}">
                        ${sev.toUpperCase()}
                    </td>
                    <td class="no-wrap" title="${issue.file || 'unknown'}">
                        ${issue.file || 'unknown'}
                    </td>
                    <td class="no-wrap">
                        <span class="top-issue-code">${issue.code || ''}</span>
                    </td>
                    <td class="no-wrap">${issue.line || ''}</td>
                    <td class="msg-col">${issue.message || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        handleSort('severity');

    } catch (e) {
        console.error(e);
        document.body.innerHTML =
            `<h3 style="color:red">Error rendering dashboard: ${e.message}</h3>`;
    }
</script>
</body>
</html>
""".replace(
            "{{DATA_JSON}}", data_json
        )

        dashboard_file.write_text(html, encoding="utf-8")
