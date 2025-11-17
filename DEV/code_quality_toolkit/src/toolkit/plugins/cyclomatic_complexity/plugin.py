"""Cyclomatic complexity plugin with a lightweight heuristic."""

from __future__ import annotations

import ast
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


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

    def configure(self, config: ToolkitConfig) -> None:
        self.max_complexity = config.rules.max_complexity

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "CyclomaticComplexity",
            "version": "0.1.0",
            "description": "Conta decisões em funções para estimar complexidade.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
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
                    severity = "medium"
                    if (complexity <= self.max_complexity+4):
                        severity = "high"
                    d = {}
                    d["severity"] = severity
                    d["code"] = "HIGH_COMPLEXITY"
                    d["message"] = f"Função '{node.name}' com complexidade {complexity}"
                    d["line"] = node.lineno
                    d["col"] = 0
                    d["hint"] = f"Reduza para <= {self.max_complexity}"
                    results.append(d)
        return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                    },
                }


# EXTENSION-POINT: suportar métricas adicionais como tamanho
# de funções ou número de argumentos.
