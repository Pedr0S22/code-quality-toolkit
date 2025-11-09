"""Cyclomatic complexity plugin with a lightweight heuristic."""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

def _function_length(node: ast.AST) -> Optional[int]:
    """Calcula o numero de linhas em funcao."""
    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        return node.end_lineno - node.lineno + 1
    return None



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

    def configure(self, config: ToolkitConfig) -> None:
        self.max_complexity = config.rules.max_complexity
        self.max_function_length = config.rules.max_function_length

    def get_metadata(self) -> Dict[str, str]:
        return {
            "name": "CyclomaticComplexity",
            "version": "0.1.0",
            "description": "Conta decisões em funções para estimar complexidade.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
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

        results: List[IssueResult] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = _ComplexityVisitor()
                visitor.visit(node)
                complexity = visitor.complexity
                if complexity > self.max_complexity:
                    severity = "medium" if complexity <= self.max_complexity + 4 else "high"
                    results.append(
                        {
                            "severity": severity,
                            "code": "HIGH_COMPLEXITY",
                            "message": f"Função '{node.name}' com complexidade {complexity}",
                            "line": node.lineno,
                            "col": 0,
                            "hint": f"Reduza para <= {self.max_complexity}",
                        }
                    )
                function_length = _function_length(node)
                if (function_length is not None and function_length > self.max_function_length):
                    severity = "low" if function_length <= self.max_function_length + 20 else "medium"
                    results.append(
                        {
                            "severity": severity,
                            "code": "LONG_FUNCTION",
                            "message": f"Function '{node.name}' with ({function_length} lines)",
                            "line": node.lineno,
                            "col": 0,
                            "hint": f"Consider dividing to smaller functions (<= {self.max_function_length} lines).",
                        }
                    )

        return {
            "results": results,
            "summary": {
                "issues_found": len(results),
                "status": "completed",
            },
        }


# EXTENSION-POINT: suportar métricas adicionais como tamanho de funções ou número de argumentos.
