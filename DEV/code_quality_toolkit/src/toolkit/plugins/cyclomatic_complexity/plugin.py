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
        # plugin_folder = pathlib.Path(__file__).parent
        # dashboard_file = plugin_folder / f"{plugin_folder.name}_dashboard.html"

        # Dashboard generation logic
        # html_content = f"<html><body><h1>Dashboard Example</h1>
        # <p>Issues found: {len(results)}</p></body></html>"

        # dashboard_file.write_text(html_content, encoding="utf-8")

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
