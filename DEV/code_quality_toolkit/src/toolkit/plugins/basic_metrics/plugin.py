# ------------------------ #
#   Basic metrics plugin   #
# ------------------------ #

from __future__ import annotations

from typing import Any, Dict

import ast
import io
import tokenize

# Imports antigos mantidos como comentário para histórico:
# import os
# import tempfile
# from radon.raw import analyze as raw_analyze
# from radon.metrics import h_visit, HalsteadReport

from ...utils.config import ToolkitConfig
from ...core.contracts import IssueResult


def issue() -> None:
    """Placeholder mantido apenas para compatibilidade."""
    pass


class Plugin:
    """
    Basic Metrics Plugin

    - Conta linhas totais, lógicas, de comentário, em branco e docstrings
    - Calcula métricas de Halstead (via radon, se disponível)
    - Devolve sempre as métricas em summary["metrics"]
    """

    def __init__(self) -> None:
        self.report_level = "LOW"

    # ------------------------------------------------------------------
    # Metadados e configuração
    # ------------------------------------------------------------------
    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "BasicMetrics",
            "version": "1.0.0",
            "description": (
                "Reports basic code metrics like LOC, comments, docstrings "
                "and Halstead metrics."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        # Mantemos esta API porque o restante toolkit usa isto.
        if hasattr(config.rules, "metrics_report_level"):
            self.report_level = config.rules.metrics_report_level

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _count_comment_lines(self, source_code: str) -> int:
        """
        Conta linhas de comentário verdadeiras usando tokenize.

        Isto conta:
        - linhas só com `# ...`
        - comentários inline: `return x + y  # comentário`

        Mas NÃO conta docstrings (são tokens STRING, não COMMENT).
        """
        comment_lines: set[int] = set()

        buf = io.StringIO(source_code)
        try:
            for tok in tokenize.generate_tokens(buf.readline):
                if tok.type == tokenize.COMMENT:
                    comment_lines.add(tok.start[0])
        except tokenize.TokenError:
            # Fallback simples caso o código esteja muito partido
            for lineno, line in enumerate(source_code.splitlines(), start=1):
                if line.lstrip().startswith("#"):
                    comment_lines.add(lineno)

        return len(comment_lines)

    def _count_docstring_lines(self, source_code: str) -> int:
        """
        Conta linhas pertencentes a docstrings "verdadeiros" (módulo, funções, classes).
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return 0

        doc_lines = 0

        # Candidatos que podem ter docstring: módulo, funções, classes.
        candidates = [tree] + [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]

        for node in candidates:
            doc = ast.get_docstring(node, clean=False)
            if doc:
                doc_lines += len(doc.splitlines())

        return doc_lines

    def _compute_raw_metrics(self, source_code: str) -> Dict[str, int]:
        """
        Usa radon.raw.analyze se estiver disponível para LOC/LLOC/blank,
        mas calcula comment_lines e docstring_lines à parte, de forma mais
        controlada e compatível com os testes.
        """
        raw = None
        try:
            from radon.raw import analyze as raw_analyze  # type: ignore[import]

            try:
                raw = raw_analyze(source_code)
            except Exception:
                raw = None
        except Exception:
            raw = None

        lines = source_code.splitlines()

        if raw is not None:
            total_lines = int(raw.loc)
            logical_lines = int(raw.lloc)
            blank_lines = int(raw.blank)
        else:
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if not line.strip())
            # Aproximação: linhas não em branco
            logical_lines = total_lines - blank_lines

        comment_lines = self._count_comment_lines(source_code)
        docstring_lines = self._count_docstring_lines(source_code)

        return {
            "total_lines": total_lines,
            "logical_lines": logical_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "docstring_lines": docstring_lines,
        }

    def _compute_halstead_metrics(self, source_code: str) -> Dict[str, float]:
        """
        Calcula métricas de Halstead via radon.metrics.h_visit, se estiver instalado.

        Se radon não estiver disponível (como no job de coverage), devolve {}.
        """
        try:
            from radon.metrics import h_visit  # type: ignore[import]
        except Exception:
            return {}

        try:
            report = h_visit(source_code)
        except Exception:
            return {}

        total = report.total

        return {
            "halstead_volume": float(total.volume),
            "halstead_difficulty": float(total.difficulty),
            "halstead_effort": float(total.effort),
        }

    # ------------------------------------------------------------------
    # Método principal exigido pelo toolkit
    # ------------------------------------------------------------------
    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        try:
            results: list[IssueResult] = []

            # ----------------- Métricas básicas -----------------
            raw_metrics = self._compute_raw_metrics(source_code)
            halstead_metrics = self._compute_halstead_metrics(source_code)

            # Este é o dicionário que os testes usam:
            metrics: Dict[str, Any] = {**raw_metrics, **halstead_metrics}

            total_lines = raw_metrics["total_lines"] or 0

            # Usamos só as métricas "de linhas" para gerar avisos.
            # Nomes ajustados para bater certo com os testes:
            inspect_metrics = {
                "total_lines": raw_metrics["total_lines"],
                "logical_lines": raw_metrics["logical_lines"],
                "comment_lines": raw_metrics["comment_lines"],
                "blank_lines": raw_metrics["blank_lines"],
                "docstring_lines": raw_metrics["docstring_lines"],
            }

            for key, value in inspect_metrics.items():
                res: IssueResult = {
                    "severity": "low",
                    "code": key,
                    "message": f"{key.replace('_', ' ').title()}: {value}",
                    "hint": "",
                }

                # Evita divisão por zero se o ficheiro estiver vazio
                percent = (value / total_lines * 100) if total_lines > 0 else 0.0

                # total_lines thresholds
                if key == "total_lines":
                    if value > 3000:
                        res["severity"] = "high"
                        res["hint"] = (
                            "File is larger than 3000 lines, consider splitting "
                            "functionality across multiple files."
                        )
                    elif value > 2000:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "File is larger than 2000 lines, consider splitting "
                            "functionality across multiple files."
                        )
                    elif value > 1000:
                        res["hint"] = (
                            "File is larger than 1000 lines, consider splitting "
                            "functionality across multiple files."
                        )
                    else:
                        # Sem problema → não criar issue
                        continue

                # logical_lines
                elif key == "logical_lines":
                    if value > 300:
                        res["severity"] = "high"
                        res["hint"] = (
                            "Very large logical code blocks. Consider splitting "
                            "into smaller functions."
                        )
                    elif value > 200:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "Long logical blocks. Consider splitting into "
                            "smaller functions."
                        )
                    elif value > 100:
                        res["hint"] = (
                            "Logical size is manageable but consider splitting "
                            "into smaller functions."
                        )
                    else:
                        continue

                # comment_lines – AGORA conta também comentários inline via tokenize
                elif key == "comment_lines":
                    if percent < 2:
                        res["severity"] = "high"
                        res["hint"] = (
                            "Very few comments. Add documentation to "
                            "improve readability."
                        )
                    elif percent < 5:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "Low comment count, consider adding documentation."
                        )
                    elif percent < 10:
                        res["hint"] = "Consider adding documentation."
                    else:
                        continue

                # blank_lines
                elif key == "blank_lines":
                    if value < 1:
                        res["severity"] = "high"
                        res["hint"] = "No blank lines. Seriously?"
                    elif percent < 5:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "Very few blank lines. Consider adding spacing "
                            "to improve readability."
                        )
                    elif percent < 10:
                        res["hint"] = (
                            "Consider adding spacing to improve readability."
                        )
                    else:
                        continue

                # docstring_lines
                elif key == "docstring_lines":
                    if percent < 2:
                        res["severity"] = "high"
                        res["hint"] = (
                            "Very few docstrings. Add documentation for "
                            "functions and classes."
                        )
                    elif percent < 4:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "Low docstring count, consider adding documentation."
                        )
                    elif percent < 8:
                        res["hint"] = (
                            "Consider adding docstrings for functions and classes."
                        )
                    else:
                        continue

                results.append(res)

            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                    "metrics": metrics,
                },
            }

        except Exception as e:
            # Caso algo corra muito mal, devolvemos um relatório marcado como failed
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Internal error in BasicMetrics: {str(e)}",
                    "metrics": {},
                },
            }
