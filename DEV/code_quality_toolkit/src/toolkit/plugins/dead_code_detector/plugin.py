"""Dead code detector plugin"""

from __future__ import annotations

import ast
import re
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class _DefUseVisitor(ast.NodeVisitor):
    """Coleta definições e usos intra-ficheiro (escopo de módulo)."""

    def __init__(self) -> None:
        self.defs: dict[str, int] = {}  # nome -> linha onde foi definido
        self.uses: set[str] = set()
        self.imports: set[str] = set()

    # ---- definições ----
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # opcional: também sinalizamos classes não usadas
        self.defs[node.name] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defs[target.id] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.defs[node.target.id] = getattr(node, "lineno", 0) or 0
        self.generic_visit(node)

    # ---- importados (não reportar nomes importados) ----
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imports.add(alias.asname or alias.name)

    # ---- usos ----
    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.uses.add(node.id)
        self.generic_visit(node)


class Plugin:
    """Plugin que deteta 'dead code'."""

    def __init__(self) -> None:
        # valores por omissão; podem ser alterados via toolkit.toml
        self.ignore_patterns: list[re.Pattern[str]] = [
            re.compile(r"^__")
        ]  # ignora dunders
        self.severity: str = "low"
        self.min_name_len: int = 1

    def configure(self, config: ToolkitConfig) -> None:
        """Recebe parâmetros de [plugins.dead_code] do toolkit.toml."""
        sect = getattr(getattr(config, "plugins", None), "dead_code", None)
        if not sect:
            return
        pats = getattr(sect, "ignore_patterns", [])
        if isinstance(pats, list):
            compiled = [re.compile(p) for p in pats]
            if compiled:
                self.ignore_patterns = compiled
        self.severity = getattr(sect, "severity", self.severity)
        self.min_name_len = int(getattr(sect, "min_name_length", self.min_name_len))

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DeadCodeDetector",
            "version": "0.1.0",
            "description": "Deteta funções, classes e variáveis definidas e "
            + "nunca usadas no mesmo ficheiro.",
        }

    # helpers
    def _ignored(self, name: str) -> bool:
        if len(name) < self.min_name_len:
            return True
        for rx in self.ignore_patterns:
            if rx.search(name):
                return True
        return False

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        # 1) Parse seguro
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
                        "hint": "Corrija a sintaxe para permitir a "
                        + "análise de dead code.",
                    }
                ],
                "summary": {"issues_found": 1, "status": "partial"},
            }

        # 2) Coleta defs/usos/imports
        v = _DefUseVisitor()
        v.visit(tree)

        # 3) Findings
        results: list[IssueResult] = []
        for name, line in v.defs.items():
            if self._ignored(name):
                continue
            if name in v.imports:
                continue
            if name not in v.uses:
                results.append(
                    {
                        "severity": self.severity,
                        "code": "DEAD_CODE",
                        "message": f"'{name}' definido e nunca usado.",
                        "line": line or 1,
                        "col": 1,
                        "hint": "Remover, utilizar, ou suprimir via "
                        + "[plugins.dead_code].ignore_patterns.",
                    }
                )

        return {
            "results": results,
            "summary": {"issues_found": len(results), "status": "completed"},
        }
