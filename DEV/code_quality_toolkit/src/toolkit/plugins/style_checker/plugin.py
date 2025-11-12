"""Simple style checking plugin."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

_SNAKE_CASE_RE = re.compile(r"^[a-z0-9_]+\.py$")


class Plugin:
    """Plugin que valida regras de estilo básicas."""

    def __init__(self) -> None:
        self.max_line_length = 88

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""

        self.max_line_length = config.rules.max_line_length

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "StyleChecker",
            "version": "0.1.0",
            "description": "Valida comprimento de linhas e convenções"
            + "simples de nomes.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        results: list[IssueResult] = []
        lines = source_code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line) > self.max_line_length:
                results.append(
                    {
                        "severity": "low",
                        "code": "LINE_LENGTH",
                        "message": f"Linha com {len(line)} caracteres",
                        "line": idx,
                        "col": 1,
                        "hint": f"Máximo configurado: {self.max_line_length}",
                    }
                )
        if file_path and not _SNAKE_CASE_RE.match(Path(file_path).name):
            results.append(
                {
                    "severity": "info",
                    "code": "FILENAME_STYLE",
                    "message": "Nome do ficheiro não segue snake_case.",
                    "line": 1,
                    "col": 1,
                    "hint": "Utilize nomes como sample_module.py",
                }
            )
        return {
            "results": results,
            "summary": {
                "issues_found": len(results),
                "status": "completed",
            },
        }


# EXTENSION-POINT: adicionar novas regras, p.ex. indentação ou trailing whitespace.
