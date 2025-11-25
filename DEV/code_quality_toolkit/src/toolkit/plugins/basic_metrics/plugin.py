# ------------------------ #
#   Basic metrics plugin   #
# ------------------------ #

from __future__ import annotations

# import os  # não usado na implementação atual do plugin basic_metrics
# import tempfile  # mantido comentado para possível uso futuro
from typing import Any

from radon.raw import analyze as raw_analyze
# from radon.metrics import h_visit, HalsteadReport  # Halstead reservado para extensões futuras
from ...utils.config import ToolkitConfig
# from ...core.contracts import IssueResult  # mantido apenas como referência ao contrato genérico


def issue() -> None:
    """Placeholder para compatibilidade com outros plugins."""
    pass


class Plugin:
    """
    Basic Metrics Plugin
    """

    def __init__(self) -> None:
        # Nível de “verbozidade”/relato vindo da config (mantido igual ao original)
        self.report_level = "LOW"

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "BasicMetrics",
            "version": "1.0.0",
            "description": "Reports basic code metrics like LOC, comments, and Halstead metrics.",
        }

    def configure(self, config: ToolkitConfig) -> None:
        # Mantido igual ao original: permite configurar o nível de reporte via config
        if hasattr(config.rules, "metrics_report_level"):
            self.report_level = config.rules.metrics_report_level

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        try:
            results: list[dict[str, Any]] = []

            # ---- Raw metrics (radon) ----
            raw = raw_analyze(source_code)
            raw_metrics = {
                "total_lines": raw.loc,
                "logical_lines": raw.lloc,
                "comment_lines": raw.comments,
                "blank_lines": raw.blank,
                "docstrings": raw.multi,
            }

            # Métricas expostas diretamente para o relatório do plugin basic_metrics.
            # Estas chaves são usadas pelos testes em tests/plugins/basic_metrics.
            metrics = {
                "total_lines": raw.loc,
                "blank_lines": raw.blank,
                "comment_lines": raw.comments,
                # docstrings multi-line (e docstrings em geral) expostas como "docstring_lines"
                "docstring_lines": raw.multi,
                # número de linhas de código segundo o cálculo de SLOC do radon
                "code_lines": raw.sloc,
            }

            total_lines = raw_metrics["total_lines"] if raw_metrics["total_lines"] > 0 else 0

            # Geração de “issues” em função de thresholds simples
            for key, value in raw_metrics.items():
                res: dict[str, Any] = {
                    "severity": "low",
                    "code": key,
                    "message": f"{key.replace('_', ' ').title()}: {value}",
                    "hint": "",
                }

                # evitar divisão por zero
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
                        # abaixo de 1000 linhas não reportamos nada
                        continue

                # logical_lines thresholds
                elif key == "logical_lines":
                    if value > 300:
                        res["severity"] = "high"
                        res["hint"] = (
                            "Very large logical code blocks. "
                            "Consider splitting into smaller functions."
                        )
                    elif value > 200:
                        res["severity"] = "medium"
                        res["hint"] = (
                            "Long logical blocks. "
                            "Consider splitting into smaller functions."
                        )
                    elif value > 100:
                        res["hint"] = (
                            "Logical size is manageable but consider splitting "
                            "into smaller functions."
                        )
                    else:
                        continue

                # comment_lines thresholds (percentagem de comentários)
                elif key == "comment_lines":
                    if percent < 2:
                        res["severity"] = "high"
                        res["hint"] = (
                            "Very few comments. Add documentation to improve readability."
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

                # blank_lines thresholds
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

                # docstrings thresholds
                elif key == "docstrings":
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

                else:
                    # métrica não conhecida → ignorar
                    continue

                results.append(res)

            # summary original, mas agora com campo "metrics" exposto
            summary: dict[str, Any] = {
                "issues_found": len(results),
                "status": "completed",
            }

            # Expor as métricas calculadas para consumo pelos testes de basic_metrics.
            summary["metrics"] = metrics

            return {
                "results": results,
                "summary": summary,
            }

        # failure
        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Internal error in BasicMetrics: {str(e)}",
                },
            }
