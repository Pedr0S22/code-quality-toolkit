# ------------------------ #
#   Basic metrics plugin   #
# ------------------------ #

from __future__ import annotations

import ast
import io
import json
import tokenize
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

# Import opcional do radon: se não estiver instalado, o plugin continua a funcionar .
try:
    from radon.metrics import h_visit
    from radon.raw import analyze as raw_analyze

    RADON_AVAILABLE = True
except Exception:  # pragma: no cover - ambiente sem radon
    raw_analyze = None
    h_visit = None
    RADON_AVAILABLE = False

# Imports antigos mantidos como comentário para histórico (pedido do enunciado):
# import os
# import tempfile
# from radon.raw import analyze as raw_analyze
# from radon.metrics import h_visit, HalsteadReport


def issue() -> None:
    """
    Função dummy mantida por compatibilidade com versões antigas do carregador
    de plugins. Não é usada nos testes atuais.
    """
    return None


class Plugin:
    """
    Basic Metrics Plugin

    Calcula métricas simples:
        - total_lines
        - logical_lines
        - comment_lines
        - blank_lines
        - docstring_lines
    e algumas métricas de Halstead (volume, dificuldade, esforço, bugs).
    As métricas ficam em summary["metrics"].
    """

    def __init__(self) -> None:
        # Nível de detalhe configurável via ToolkitConfig.rules.metrics_report_level
        self.report_level: str = "LOW"

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "BasicMetrics",
            "version": "1.0.0",
            "description": (
                "Reports basic code metrics like LOC, comments, blanks "
                "and Halstead metrics."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        sect = getattr(getattr(config, "plugins", None), "basic_metrics", None)
        self.report_level = getattr(sect, "report_level", self.report_level)

    # ------------------------------------------------------------------
    # Helpers para descobrir docstrings, comentários e linhas em branco
    # ------------------------------------------------------------------

    @staticmethod
    def _docstring_line_numbers(source_code: str) -> set[int]:
        """
        Devolve o conjunto de números de linha físicos que pertencem a docstrings.
        Usa AST para encontrar docstrings de módulo, classe e função.
        """
        doc_lines: set[int] = set()
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return doc_lines

        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                if not node.body:
                    continue

                first_stmt = node.body[0]
                if (
                    isinstance(first_stmt, ast.Expr)
                    and isinstance(first_stmt.value, ast.Constant)
                    and isinstance(first_stmt.value.value, str)
                ):
                    lineno = first_stmt.lineno
                    end_lineno = getattr(first_stmt, "end_lineno", lineno)
                    for line_no in range(lineno, end_lineno + 1):
                        doc_lines.add(line_no)

        return doc_lines

    @staticmethod
    def _count_comments_and_blanks(
        source_code: str, docstring_lines: set[int]
    ) -> tuple[int, int]:
        """
        Conta:
          - linhas de comentário (excluindo linhas de docstring)
          - linhas em branco
        """
        comment_lines: set[int] = set()

        try:
            for token in tokenize.generate_tokens(io.StringIO(source_code).readline):
                if token.type == tokenize.COMMENT:
                    line_no = token.start[0]
                    if line_no not in docstring_lines:
                        comment_lines.add(line_no)
        except tokenize.TokenError:
            # Código possivelmente incompleto – faz-se o melhor possível.
            pass

        lines = source_code.splitlines()
        blank_count = sum(1 for line in lines if not line.strip())

        return len(comment_lines), blank_count

    # ------------------------------------------------------------------
    # Helpers para calcular métricas numéricas
    # ------------------------------------------------------------------

    def _compute_raw_metrics(self, source_code: str) -> dict[str, int]:
        """
        Calcula:
            - total_lines
            - logical_lines
            - comment_lines
            - blank_lines
            - docstring_lines

        Se `radon` existir, usa radon.raw.analyze para ter valores consistentes
        com o resto do toolkit. Se não existir, usa um fallback textual simples.
        """
        doc_lines = self._docstring_line_numbers(source_code)
        comment_count, blank_count = self._count_comments_and_blanks(
            source_code, doc_lines
        )

        if RADON_AVAILABLE and raw_analyze is not None:
            raw = raw_analyze(source_code)
            return {
                "total_lines": raw.loc,
                "logical_lines": raw.lloc,
                "comment_lines": comment_count,
                "blank_lines": blank_count,
                "docstring_lines": len(doc_lines),
            }

        # Fallback sem radon: aproximação razoável.
        lines = source_code.splitlines()
        total = len(lines)
        logical = total - blank_count

        return {
            "total_lines": total,
            "logical_lines": logical,
            "comment_lines": comment_count,
            "blank_lines": blank_count,
            "docstring_lines": len(doc_lines),
        }

    def _compute_halstead_metrics(self, source_code: str) -> dict[str, float]:
        """
        Calcula algumas métricas de Halstead via radon.metrics.h_visit.
        Se radon não estiver disponível, devolve zeros estáveis.
        """
        if not (RADON_AVAILABLE and h_visit is not None):
            return {
                "h_volume": 0.0,
                "h_difficulty": 0.0,
                "h_effort": 0.0,
                "h_bugs": 0.0,
            }

        reports = list(h_visit(source_code))
        if not reports:
            return {
                "h_volume": 0.0,
                "h_difficulty": 0.0,
                "h_effort": 0.0,
                "h_bugs": 0.0,
            }

        rep = reports[0]
        return {
            "h_volume": float(getattr(rep, "volume", 0.0)),
            "h_difficulty": float(getattr(rep, "difficulty", 0.0)),
            "h_effort": float(getattr(rep, "effort", 0.0)),
            "h_bugs": float(getattr(rep, "bugs", 0.0)),
        }

    def _compute_basic_metrics(self, source_code: str) -> dict[str, Any]:
        """
        Junta métricas "raw" e Halstead num só dicionário.
        """
        raw_metrics = self._compute_raw_metrics(source_code)
        halstead_metrics = self._compute_halstead_metrics(source_code)
        metrics: dict[str, Any] = {**raw_metrics, **halstead_metrics}
        return metrics

    # ------------------------------------------------------------------
    # Helpers para gerar issues a partir das métricas
    # ------------------------------------------------------------------

    def _maybe_build_issue(
        self, metric_name: str, value: int | float, total_lines: int
    ) -> IssueResult | None:
        """
        Cria um IssueResult simples para algumas métricas.

        Mantemos esta função pequena em termos de decisões para não rebentar a
        análise de complexidade do Xenon (limite C).
        """
        # 1) total_lines – ficheiros muito grandes
        if metric_name == "total_lines":
            if value <= 1000:
                return None

            severity = "low"
            if value > 3000:
                severity = "high"
            elif value > 2000:
                severity = "medium"

            return {
                "severity": severity,
                "code": "total_lines",
                "message": f"File has {int(value)} total lines.",
                "hint": (
                    "Large files are harder to navigate; consider splitting the "
                    "module."
                ),
            }

        # 2) logical_lines – blocos lógicos muito extensos
        if metric_name == "logical_lines":
            if value <= 100:
                return None

            severity = "low"
            if value > 300:
                severity = "high"
            elif value > 200:
                severity = "medium"

            return {
                "severity": severity,
                "code": "logical_lines",
                "message": f"File has {int(value)} logical lines.",
                "hint": (
                    "Long logical blocks can often be split into smaller functions."
                ),
            }

        # 3) comment_lines – poucas linhas de comentário
        if metric_name == "comment_lines" and total_lines > 0:
            percent = (value / total_lines) * 100
            if percent >= 10:
                return None

            severity = "low"
            if percent < 2:
                severity = "high"
            elif percent < 5:
                severity = "medium"

            return {
                "severity": severity,
                "code": "comment_lines",
                "message": f"Only {percent:.1f}% of lines are comments.",
                "hint": "Consider adding more explanatory comments and docstrings.",
            }

        # blank_lines e docstring_lines não geram issues explícitos aqui.
        return None

    # ------------------------------------------------------------------
    # Entry-point principal exigido pelo engine
    # ------------------------------------------------------------------

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Analisa um ficheiro fonte e devolve:
            - lista de issues em "results"
            - métricas numéricas em "summary['metrics']"
        """
        results = {}
        try:
            metrics = self._compute_basic_metrics(source_code)
            total = int(metrics.get("total_lines", 0))

            issues: list[IssueResult] = []
            for name, val in metrics.items():
                issue_obj = self._maybe_build_issue(name, val, total)
                if issue_obj is not None:
                    issues.append(issue_obj)

            results = {
                "results": issues,
                "summary": {
                    "issues_found": len(issues),
                    "status": "completed",
                    "metrics": metrics,
                },
            }
        except Exception as exc:
            # Defesa: o plugin nunca deve mandar o engine abaixo.
            results = {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Internal error in BasicMetrics: {exc}",
                },
            }

        return results

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def generate_dashboard(self, results) -> str:
        """
        Generates the D3.js dashboard HTML file.
        """
        dashboard_file = "src/toolkit/plugins/basic_metrics/"
        dashboard_file += "basic_metrics_dashboard.html"

        try:
            html_content = self.render_html(results)

            with open(dashboard_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            return dashboard_file
        except Exception:
            return ""

    def render_html(self, results) -> str:
        """
        Prepares data and returns the final HTML dashboard with injected JSON.
        """
        dashboard_data = self._aggregate_data_for_dashboard(results)
        data_json = json.dumps(dashboard_data)
        return self._get_html_template(data_json)

    def _aggregate_data_for_dashboard(self, results):
        """
        Converts plugin results into a JSON-ready dashboard structure.
        """
        items = results.get("results", []) if isinstance(results, dict) else results

        metrics = results.get(
                "summary",
                {}).get("metrics", {}) if isinstance(results, dict) else {}

        severity_counts = {}
        for item in items:
            sev = item.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "metrics": metrics,
            "results": items,
            "severity_counts": [
                {"severity": k, "count": v} for k, v in severity_counts.items()
            ],
        }

    def _get_html_template(self, data_json: str) -> str:
        """Responsive D3.js dashboard template for Basic Metrics."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Basic Metrics Dashboard</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
body {{
    font-family: 'Segoe UI', sans-serif;
    margin: 0; padding: 20px;
    background-color: #f4f4f4;
    display: flex; justify-content: center;
}}
.chart-container {{
    width: 100%;
    max-width: 1066px;
    aspect-ratio: 1066 / 628;
    background: white;
    border: 1px solid #ccc;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    box-sizing: border-box;
}}
</style>
</head>
<body>

<div id="app" class="chart-container"></div>

<script>
const data = {data_json};
const metrics = data.metrics || {{}};
const issues = data.results || [];

const width = 1066;
const height = 628;

const svg = d3.select("#app").append("svg")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .style("width", "100%")
    .style("height", "100%")
    .style("background-color", "#fff");

// HEADER
svg.append("rect")
    .attr("x",0).attr("y",0)
    .attr("width",width).attr("height",70)
    .attr("fill","#0d6efd");

svg.append("text")
    .attr("x",20).attr("y",45)
    .attr("fill","white")
    .style("font-size","24px")
    .style("font-weight","bold")
    .text("Basic Metrics Analysis");

// METRICS PANEL (LEFT)
const mGroup = svg.append("g").attr("transform","translate(20,100)");
let idx = 0;
for (const [key,val] of Object.entries(metrics)) {{
    mGroup.append("text")
        .attr("x",0).attr("y", idx*25)
        .style("font-size","14px")
        .style("font-weight","bold")
        .text(`${{key}}: ${{val}}`);
    idx++;
}}

// ISSUES BY SEVERITY (RIGHT)
const severityCounts = data.severity_counts || [];
if (severityCounts.length) {{
    const x = d3.scaleBand()
        .domain(severityCounts.map(d=>d.severity))
        .range([550, 950])
        .padding(0.2);
    const y = d3.scaleLinear()
        .domain([0, d3.max(severityCounts,d=>d.count)])
        .range([580,150]);

    const bars = svg.append("g");
    bars.selectAll("rect")
        .data(severityCounts)
        .enter()
        .append("rect")
        .attr("x",d=>x(d.severity))
        .attr("y",d=>y(d.count))
        .attr("width",x.bandwidth())
        .attr("height",d=>580 - y(d.count))
        .attr("fill","#0d6efd");

    bars.selectAll("text")
        .data(severityCounts)
        .enter()
        .append("text")
        .attr("x",d=>x(d.severity)+x.bandwidth()/2)
        .attr("y",d=>y(d.count)-5)
        .attr("text-anchor","middle")
        .style("font-size","12px")
        .style("font-weight","bold")
        .text(d=>d.count);
}} else {{
    svg.append("text")
        .attr("x",775).attr("y",350)
        .attr("text-anchor","middle")
        .attr("fill","#28a745")
        .style("font-size","16px")
        .text("✅ No issues found!");
}}
</script>

</body>
</html>"""
