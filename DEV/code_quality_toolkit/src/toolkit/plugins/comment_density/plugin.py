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
