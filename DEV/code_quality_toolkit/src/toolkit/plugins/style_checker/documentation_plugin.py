"""Plugin para analizar la calidad de la documentación."""

import ast
from typing import Any, Dict, List, Tuple

from core.plugin_base import CodeQualityPlugin


class DocumentationPlugin(CodeQualityPlugin):
    """Analiza densidad de comentarios y docstrings."""

    def get_metadata(self) -> Dict[str, str]:
        """Retorna los metadatos del plugin."""
        return {
            "name": "DocumentationQuality",
            "version": "1.0.0",
            "author": "@Chege39226912",
            "description": "Analiza densidad de comentarios y docstrings",
        }

    def _count_docstrings(self, lines: List[str]) -> int:
        """Cuenta las líneas que forman parte de docstrings."""
        docstring_lines = 0
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                else:
                    in_docstring = True
                docstring_lines += 1
            elif in_docstring:
                docstring_lines += 1
        return docstring_lines

    def _analyze_ast(self, source_code: str) -> Tuple[int, int, int, int]:
        """Analiza el AST para contar funciones y clases documentadas."""
        functions = 0
        classes = 0
        functions_with_doc = 0
        classes_with_doc = 0

        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions += 1
                    if ast.get_docstring(node):
                        functions_with_doc += 1
                elif isinstance(node, ast.ClassDef):
                    classes += 1
                    if ast.get_docstring(node):
                        classes_with_doc += 1
        except Exception:  # nosec
            pass  # Si falla el parseo, seguimos sin crashear

        return functions, classes, functions_with_doc, classes_with_doc

    def analyze(self, source_code: str, file_path: str = None) -> Dict[str, Any]:
        """Ejecuta el análisis sobre el código fuente."""
        issues = []
        lines = source_code.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))

        docstring_lines = self._count_docstrings(lines)
        stats = self._analyze_ast(source_code)
        functions, _, functions_with_doc, _ = stats

        # Métricas
        comment_density = 0
        if total_lines > 0:
            comment_density = (comment_lines + docstring_lines) / total_lines * 100

        func_doc_ratio = 100
        if functions > 0:
            func_doc_ratio = (functions_with_doc / functions * 100)

        # Issues
        if comment_density < 15:
            severity = "low"
            if comment_density < 8:
                severity = "high"
            elif comment_density < 15:
                severity = "medium"

            issues.append({
                "file": file_path or "unknown.py",
                "entity": "file",
                "line": 1,
                "metric": "comment_density_percent",
                "value": round(comment_density, 2),
                "severity": severity,
                "code": "DOC001",
                "message": (
                    f"Densidad de comentarios baja: {comment_density:.1f}% "
                    "(min 15%)"
                ),
            })

        if functions > 0 and func_doc_ratio < 80:
            issues.append({
                "file": file_path or "unknown.py",
                "entity": "functions",
                "line": 1,
                "metric": "functions_with_docstring_percent",
                "value": round(func_doc_ratio, 1),
                "severity": "high",
                "code": "DOC002",
                "message": (
                    f"Solo {functions_with_doc}/{functions} funcs tienen doc "
                    f"({func_doc_ratio:.1f}%)."
                ),
            })

        return {
            "plugin": self.get_metadata(),
            "results": issues,
            "summary": {
                "issues_found": len(issues),
                "status": "completed",
            },
        }