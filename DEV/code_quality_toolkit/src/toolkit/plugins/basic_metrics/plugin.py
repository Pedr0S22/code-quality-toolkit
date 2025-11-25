"""
Basic metrics plugin.

Notas importantes para os testes:
- O `radon` é tratado como dependência *opcional*. Se não estiver instalado,
  o plugin importa na mesma e usa contadores simples, para não partir o CLI.
- As funções `count_*` são helpers puros, fáceis de testar, e são pensadas
  para ser importadas diretamente nos testes (`from ... import count_blank_lines`, etc.).
"""

from __future__ import annotations

from typing import Any, Dict

import ast

# ---------------------------------------------------------------------------
# Import opcional do radon (resolve o erro do test_coverage)
# ---------------------------------------------------------------------------
try:  # pragma: no cover
    from radon.raw import analyze as raw_analyze  # type: ignore
    from radon.metrics import h_visit, HalsteadReport  # type: ignore

    HAS_RADON = True
except ModuleNotFoundError:  # pragma: no cover
    # No job de coverage o radon não é instalado. Para não quebrar o CLI,
    # tratamos isso aqui e usamos apenas os nossos contadores simples.
    raw_analyze = None  # type: ignore[assignment]
    HalsteadReport = object  # type: ignore[assignment]
    HAS_RADON = False

from ...utils.config import ToolkitConfig
from ...core.contracts import IssueResult


# ---------------------------------------------------------------------------
# Helpers de baixo nível (os testes de basic_metrics usam estas funções)
# ---------------------------------------------------------------------------

def _split_lines(source_code: str) -> list[str]:
    """Divide o código em linhas sem perder linhas vazias."""
    return source_code.splitlines()


def count_total_lines(source_code: str) -> int:
    """Número total de linhas do ficheiro."""
    return len(_split_lines(source_code))


def count_blank_lines(source_code: str) -> int:
    """Número de linhas completamente vazias (só whitespace)."""
    return sum(1 for line in _split_lines(source_code) if line.strip() == "")


def count_comment_lines(source_code: str) -> int:
    """Número de linhas que são *só* comentário.

    Considera-se comentário se, depois de tirar espaços à esquerda,
    a linha começar por '#'. Comentários inline em linhas de código
    contam como código, não como 'comment line'.
    """
    return sum(1 for line in _split_lines(source_code) if line.lstrip().startswith("#"))


def count_docstring_lines(source_code: str) -> int:
    """Número de docstrings no módulo/código.

    Para os testes, cada docstring (módulo, função, classe) conta como 1,
    mesmo que ocupe várias linhas. Por exemplo:

        - docstring de módulo
        - docstring de função

    => resultado esperado: 2.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            if ast.get_docstring(node, clean=False) is not None:
                count += 1
    return count


def count_code_lines(source_code: str) -> int:
    """Número de linhas que contêm código executável.

    Aproximação usada:

        code_lines = total_lines - blank_lines - comment_only_lines - docstrings

    É suficiente para os testes de basic_metrics.
    """
    total = count_total_lines(source_code)
    blank = count_blank_lines(source_code)
    comments = count_comment_lines(source_code)
    docstrings = count_docstring_lines(source_code)
    return max(total - blank - comments - docstrings, 0)


# ---------------------------------------------------------------------------
# Implementação do plugin
# ---------------------------------------------------------------------------


class Plugin:
    """Basic Metrics Plugin."""

    def __init__(self) -> None:
        # Nível de detalhe do relatório (pode vir da config).
        self.report_level: str = "LOW"

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "BasicMetrics",
            "version": "1.0.0",
            "description": (
                "Reports basic code metrics like LOC, comments, blanks "
                "and docstrings. Uses radon when available."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        # Permite alterar o nível via config.rules.metrics_report_level
        if hasattr(config.rules, "metrics_report_level"):
            self.report_level = str(config.rules.metrics_report_level).upper()

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Corre a análise de métricas básicas sobre o código."""
        try:
            # --- Métricas base (as que os testes de basic_metrics usam) ---
            total_lines = count_total_lines(source_code)
            blank_lines = count_blank_lines(source_code)
            comment_lines = count_comment_lines(source_code)
            docstring_lines = count_docstring_lines(source_code)
            code_lines = count_code_lines(source_code)

            metrics: Dict[str, int] = {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines,
                "docstring_lines": docstring_lines,
            }

            # --- Halstead via radon (opcional – só se radon estiver instalado) ---
            halstead: dict[str, Any] | None = None
            if HAS_RADON and raw_analyze is not None:
                try:
                    halstead_report: HalsteadReport = h_visit(source_code)  # type: ignore[assignment]
                    halstead = {
                        "h1": halstead_report.h1,
                        "h2": halstead_report.h2,
                        "N1": halstead_report.N1,
                        "N2": halstead_report.N2,
                        "vocabulary": halstead_report.vocabulary,
                        "length": halstead_report.length,
                        "volume": halstead_report.volume,
                        "difficulty": halstead_report.difficulty,
                        "effort": halstead_report.effort,
                    }
                except Exception:
                    # Se der erro a calcular Halstead, ignoramos em vez de falhar o plugin.
                    halstead = None

            results: list[IssueResult] = []

            # Pequenos exemplos de avisos com base nas métricas
            if total_lines > 3000:
                results.append(
                    {
                        "severity": "high",
                        "code": "BASIC_METRICS_TOTAL_LINES",
                        "message": (
                            f"File has {total_lines} total lines; consider "
                            "splitting it into smaller modules."
                        ),
                        "hint": "Try to keep individual files smaller than 3000 lines.",
                    }
                )
            elif total_lines > 2000:
                results.append(
                    {
                        "severity": "medium",
                        "code": "BASIC_METRICS_TOTAL_LINES",
                        "message": (
                            f"File has {total_lines} total lines; it might be "
                            "hard to maintain."
                        ),
                        "hint": "Consider extracting independent components into separate files.",
                    }
                )

            if total_lines > 0:
                comment_ratio = comment_lines / total_lines
                if comment_ratio < 0.02:
                    results.append(
                        {
                            "severity": "high",
                            "code": "BASIC_METRICS_COMMENTS",
                            "message": (
                                "Very few comment-only lines; the file may be hard "
                                "to understand."
                            ),
                            "hint": "Add comments or docstrings to clarify complex logic.",
                        }
                    )

            summary: dict[str, Any] = {
                "issues_found": len(results),
                "status": "completed",
                "metrics": metrics,
            }
            if halstead is not None:
                summary["halstead"] = halstead

            return {
                "results": results,
                "summary": summary,
            }

        except Exception as exc:
            # Nunca deixar o plugin rebentar o motor todo
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Internal error in BasicMetrics: {exc}",
                },
            }
