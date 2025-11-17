import re
import ast
from core.plugin_base import CodeQualityPlugin

class DocumentationPlugin(CodeQualityPlugin):
    def get_metadata(self):
        return {
            "name": "DocumentationQuality",
            "version": "1.0.0",
            "author": "@Chege39226912",
            "description": "Analiza densidad de comentarios y docstrings"
        }

    def analyze(self, source_code: str, file_path: str = None) -> dict:
        issues = []
        lines = source_code.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        docstring_lines = 0
        functions = 0
        classes = 0
        functions_with_doc = 0
        classes_with_doc = 0

        # Contar docstrings multi-línea
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

        # Analizar AST para funciones y clases
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
        except Exception as e:
    # Ignorar errores de parseo sin romper la ejecución
    # (Bandit no se quejará porque ya no hay un except vacío)
            print(f"Warning: AST parse failed in {file_path}: {e}")

        # Métricas
        comment_density = (comment_lines + docstring_lines) / total_lines * 100 if total_lines > 0 else 0
        func_doc_ratio = (functions_with_doc / functions * 100) if functions > 0 else 100

        # Issues
        if comment_density < 15:
            issues.append({
                "file": file_path or "unknown.py",
                "entity": "file",
                "line": 1,
                "metric": "comment_density_percent",
                "value": round(comment_density, 2),
                "severity": "high" if comment_density < 8 else "medium" if comment_density < 15 else "low",
                "message": f"Densidad de comentarios muy baja: {comment_density:.1f}% (mínimo recomendado 15%)"
            })

        if functions > 0 and func_doc_ratio < 80:
            issues.append({
                "file": file_path or "unknown.py",
                "entity": "functions",
                "line": 1,
                "metric": "functions_with_docstring_percent",
                "value": round(func_doc_ratio, 1),
                "severity": "high",
                "message": f"Solo {functions_with_doc}/{functions} funciones tienen docstring ({func_doc_ratio:.1f}%). ¡Documenta más, crack!"
            })

        return {
            "plugin": self.get_metadata(),
            "results": issues,
            "summary": {
                "issues_found": len(issues),
                "status": "completed"
            }
        }