"""Plugin que procura por codigo duplicado."""

from typing import Any
import subprocess

from ...core.contracts import IssueResult
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

        # Run pylint duplicate-code checker
        proc = subprocess.run(
            [
                "pylint",
                "--disable=all",
                "--enable=R0801",
                "--msg-template='{line}|{column}|{msg_id}|{msg}'",
                file_path,
            ],
            capture_output=True,
            text=True,
        )

        results = []

        for line in proc.stdout.splitlines():
            try:
                row, col, code, text = line.strip().strip("'").split("|", 3)
            except ValueError:
                continue

            results.append({
                "plugin": self.get_metadata()["name"],
                "file": file_path,
                "entity": "bloco duplicado",
                "line_numbers": [int(row)],
                "similarity": 100,
                "refactoring_suggestion": "Consolidar bloco",
                "details": {
                    "occurrences": 1,
                    "message": text,
                },
                "metric": "duplicate_code",
                "value": None,
                "severity": "medium",
                "code": code,
                "message": text,
                "line": int(row),
                "col": int(col),
                "hint": "Refactor to remove repeated logic.",
            })

        summary = {"issues_found": len(results), "status": "completed"}

        summary_entry = {
            "plugin": self.get_metadata()["name"],
            "file": file_path,
            "entity": "bloco duplicado",
            "line_numbers": [r["line"] for r in results],
            "details": {
                "occurrences": len(results),
                "message": f"Found {len(results)} duplicated code blocks.",
            },
            "metric": "duplicate_code",
            "value": None,
            "severity": "high" if len(results) > 2 else "medium",
            "code": "DUPLICATED_CODE",
            "message": "Multiple duplicated code blocks found.",
            "line": results[0]["line"] if results else 0,
            "col": 0,
            "hint": "Consider refactoring to reduce code duplication.",
            "summary": summary,
        }

        return {
            "plugin": self.get_metadata()["name"],
            "results": results + [summary_entry],
            "summary": summary,
        }
