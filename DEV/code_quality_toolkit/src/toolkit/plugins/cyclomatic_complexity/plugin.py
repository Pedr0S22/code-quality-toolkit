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
        """
        Lê as configurações da nova secção específica [plugins.cyclomatic_complexity].
        Isto cumpre o requisito de estruturar melhor as regras.
        """
        # 1. Obter a configuração específica deste plugin
        # Agora procuramos explicitamente por 'cyclomatic_complexity'
        plugin_config = config.plugins.get("cyclomatic_complexity", {})

        # 2. Atualizar os limites se estiverem definidos no TOML
        if "max_complexity" in plugin_config:
            self.max_complexity = plugin_config["max_complexity"]

        if "max_function_length" in plugin_config:
            self.max_function_length = plugin_config["max_function_length"]

        if "max_arguments" in plugin_config:
            self.max_arguments = plugin_config["max_arguments"]

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "CyclomaticComplexity",
            # A imagem mostrava 0.2.0, por isso subimos para 0.3.0 conforme pedido
            "version": "0.3.0", 
            "description": "Cyclomatic complexity plugin with a lightweight heuristic.",
        }


    # --- 1) ler valores de [rules]  ---
    if hasattr(self.config, "rules"):
        if getattr(config.rules, "max_complexity", None) is not None:
            self.max_complexity = config.rules.max_complexity

        if getattr(config.rules, "max_function_length", None) is not None:
            self.max_function_length = config.rules.max_function_length

        if getattr(config.rules, "max_arguments", None) is not None:
            self.max_arguments = config.rules.max_arguments

    # --- 2) ler valores de [plugins.cyclomatic_complexity] ---
    plugin_cfg = config.plugins.get("cyclomatic_complexity", {})

    if "max_complexity" in plugin_cfg:
        self.max_complexity = plugin_cfg["max_complexity"]

    if "max_function_length" in plugin_cfg:
        self.max_function_length = plugin_cfg["max_function_length"]

    if "max_arguments" in plugin_cfg:
        self.max_arguments = plugin_cfg["max_arguments"]


    


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
