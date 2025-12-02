"""Plugin que procura por codigo duplicado."""

from __future__ import annotations

import subprocess  # nosec B404 - uso controlado do módulo subprocess para chamar pylint
import sys
from pathlib import Path
from typing import Any

from ...utils.config import ToolkitConfig


class Plugin:
    def __init__(self) -> None:
        self.max_complexity = 10

    def configure(self, config: ToolkitConfig) -> None:
        self.max_line_length = config.rules.max_line_length

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DuplicationChecker",
            "version": "0.1.0",
            "description": "Detects duplicated code using pylint R0801",
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        if not file_path:
            return {"error": "file_path required"}

        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Invalid path: {file_path}")

        # If it's a directory, gather all .py files
        if path_obj.is_dir():
            files_to_check = [str(p) for p in path_obj.rglob("*.py")]
        else:
            files_to_check = [str(path_obj)]

        if not files_to_check:
            return {
                "plugin": self.get_metadata()["name"],
                "results": [],
                "summary": {"issues_found": 0, "status": "completed"},
            }

        # Run pylint on all files at once
        proc = subprocess.run(  # nosec B603 - chamada a pylint com argumentos fixos, sem dados não confiáveis
            [
                sys.executable,
                "-m",
                "pylint",
                "--disable=all",
                "--enable=R0801",
                *files_to_check,
            ],
            capture_output=True,
            text=True,
        )

        results = []
        for line in proc.stdout.splitlines():
            try:
                path_part, line_part, col_part, rest = line.split(":", 3)
                row = int(line_part)
                col = int(col_part)
                code = "R0801"
                message = rest.strip()
            except (ValueError, IndexError):
                continue

            results.append(
                {
                    "plugin": self.get_metadata()["name"],
                    "file": path_part,
                    "entity": "bloco duplicado",
                    "line_numbers": [row],
                    "similarity": 100,
                    "refactoring_suggestion": "Consolidar bloco",
                    "details": {"occurrences": 1, "message": message},
                    "metric": "duplicate_code",
                    "value": None,
                    "severity": "medium",
                    "code": code,
                    "message": message,
                    "line": row,
                    "col": col,
                    "hint": "Refactor to remove repeated logic.",
                }
            )

        summary = {"issues_found": len(results), "status": "completed"}

        return {
            "plugin": self.get_metadata()["name"],
            "results": results,
            "summary": summary,
        }
