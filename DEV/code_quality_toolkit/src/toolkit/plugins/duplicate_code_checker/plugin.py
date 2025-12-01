"""Plugin que procura por codigo duplicado."""

from typing import Any
import subprocess, sys

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

        # Run pylint for R0801 duplicates
        # Use --output-format=text and parse lines containing "R0801"
        proc = subprocess.run(
            [sys.executable, "-m", "pylint", "--disable=all", "--enable=R0801", file_path],
            capture_output=True,
            text=True,
        )

        results = []

        for line in proc.stdout.splitlines():
            # Example Pylint R0801 line:
            # duplicate_code_checker.py:2:0: R0801: Similar lines in 2 files
            if "R0801" in line:
                try:
                    path_part, line_part, col_part, rest = line.split(":", 3)
                    row = int(line_part)
                    col = int(col_part)
                    code = "R0801"
                    message = rest.strip()
                except Exception:
                    # Skip lines we can't parse
                    continue

                results.append({
                    "plugin": self.get_metadata()["name"],
                    "file": file_path,
                    "entity": "bloco duplicado",
                    "line_numbers": [row],
                    "similarity": 100,
                    "refactoring_suggestion": "Consolidar bloco",
                    "details": {
                        "occurrences": 1,
                        "message": message,
                    },
                    "metric": "duplicate_code",
                    "value": None,
                    "severity": "medium",
                    "code": code,
                    "message": message,
                    "line": row,
                    "col": col,
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
            "message": "Multiple duplicated code blocks found." if results else "",
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
