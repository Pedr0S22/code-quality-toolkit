"""Cyclomatic complexity plugin with a lightweight heuristic."""

from __future__ import annotations

import ast
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


def _function_length(node: ast.AST) -> int | None:
    """Calcula o numero de linhas em funcao."""
    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        return node.end_lineno - node.lineno + 1
    return None


def _arg_count(fn: ast.AST) -> int:
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return 0
    a = fn.args
    total = 0
    total += len(getattr(a, "posonlyargs", []))
    total += len(a.args)
    total += len(a.kwonlyargs)
    total += 1 if a.vararg else 0
    total += 1 if a.kwarg else 0
    return total


class _ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1

    def generic_visit(self, node: ast.AST) -> None:  # noqa: D401 - inherited docs
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.With,
                ast.BoolOp,
                ast.And,
                ast.Or,
                ast.ExceptHandler,
            ),
        ):
            self.complexity += 1
        super().generic_visit(node)


class Plugin:
    """Calcula complexidade ciclomática aproximada por função."""

    def __init__(self) -> None:
        self.max_complexity = 10
        self.max_function_length = 50
        self.max_arguments = 5

    def configure(self, config: ToolkitConfig) -> None:
        self.max_complexity = config.rules.max_complexity
        self.max_function_length = config.rules.max_function_length
        self.max_arguments = config.rules.max_arguments

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "CyclomaticComplexity",
            "version": "0.1.0",
            "description": "Conta decisões em funções para estimar complexidade.",
        }

    def generate_dashboard(self, results: list[IssueResult]):
        """
        Generates the D3.js CyclomaticComplexity dashboard HTML file.
        """

        plugin_folder = pathlib.Path(__file__).parent
        dashboard_file = plugin_folder / "cyclomatic_complexity_dashboard.html"

        total_issues = len(results)

        severity_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for issue in results:
            sev = issue.get("severity", "").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        dashboard_data = {
            "total_issues": total_issues,
            "severity_counts": severity_counts,
        }

        html_content = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cyclomatic Complexity Dashboard</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
            }}
            #dashboard {{
                width: 1066px;
                height: 628px;
                padding: 20px;
                box-sizing: border-box;
            }}
            .bar {{
                fill: steelblue;
            }}
            .label {{
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
    <div id="dashboard">
        <h2>Cyclomatic Complexity Dashboard</h2>
        <p><strong>Total issues:</strong> {total_issues}</p>
        <svg width="600" height="400"></svg>
    </div>

    <script>
    const data = {json.dumps(dashboard_data["severity_counts"])};

    const svg = d3.select("svg");
    const margin = {{top: 40, right: 20, bottom: 40, left: 60}};
    const width = +svg.attr("width") - margin.left - margin.right;
    const height = +svg.attr("height") - margin.top - margin.bottom;

    const g = svg.append("g")
        .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

    const entries = Object.entries(data);

    const x = d3.scaleBand()
        .domain(entries.map(d => d[0]))
        .range([0, width])
        .padding(0.3);

    const y = d3.scaleLinear()
        .domain([0, d3.max(entries, d => d[1]) || 1])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${{height}})`)
        .call(d3.axisBottom(x));

    g.append("g")
        .call(d3.axisLeft(y));

    g.selectAll(".bar")
        .data(entries)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d[0]))
        .attr("y", d => y(d[1]))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d[1]));

    g.selectAll(".label")
        .data(entries)
        .enter()
        .append("text")
        .attr("class", "label")
        .attr("x", d => x(d[0]) + x.bandwidth() / 2)
        .attr("y", d => y(d[1]) - 5)
        .attr("text-anchor", "middle")
        .text(d => d[1]);
    </script>
    </body>
    </html>
    """

        return html_content


    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Run the analysis on a single file.
        This function MUST NOT raise an exception.
        """

        try:
            # SyntaxError logic
            try:
                tree = ast.parse(source_code)
            except SyntaxError as exc:
                return {
                    "results": [
                        {
                            "severity": "high",
                            "code": "SYNTAX_ERROR",
                            "message": f"Erro de sintaxe: {exc}",
                            "line": exc.lineno or 0,
                            "col": exc.offset or 0,
                            "hint": "Corrija a sintaxe antes de medir complexidade.",
                        }
                    ],
                    "summary": {"issues_found": 1, "status": "partial"},
                }

            results: list[IssueResult] = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visitor = _ComplexityVisitor()
                    visitor.visit(node)
                    complexity = visitor.complexity
                    if complexity > self.max_complexity:
                        severity = (
                            "medium"
                            if complexity <= self.max_complexity + 4
                            else "high"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "HIGH_COMPLEXITY",
                                "message": f"Função '{node.name}' com complexidade "
                                + f"{complexity}",
                                "line": node.lineno,
                                "col": 0,
                                "hint": f"Reduza para <= {self.max_complexity}",
                            }
                        )
                    function_length = _function_length(node)
                    if (
                        function_length is not None
                        and function_length > self.max_function_length
                    ):
                        severity = (
                            "low"
                            if function_length <= self.max_function_length + 20
                            else "medium"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "LONG_FUNCTION",
                                "message": f"Function '{node.name}' with "
                                + f"({function_length} lines)",
                                "line": node.lineno,
                                "col": 0,
                                "hint": "Consider dividing to smaller functions "
                                + f"(<= {self.max_function_length} lines).",
                            }
                        )
                    arg_count = _arg_count(node)
                    if arg_count > self.max_arguments:
                        severity = (
                            "low" if arg_count <= self.max_arguments + 2 else "medium"
                        )
                        results.append(
                            {
                                "severity": severity,
                                "code": "TOO_MANY_ARGUMENTS",
                                "message": f"Function '{node.name}' with "
                                + f"({arg_count} arguments)",
                                "line": node.lineno,
                                "col": 0,
                                "hint": "Consider reducing number of arguments "
                                + f"(<= {self.max_arguments}).",
                            }
                        )

            # Return a standard Success Response
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        # This 'except' block  catches any other unexpected behaviour
        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }
