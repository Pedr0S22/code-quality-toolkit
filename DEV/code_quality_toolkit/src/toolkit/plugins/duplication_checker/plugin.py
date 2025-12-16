"""Plugin que procura por codigo duplicado."""

from __future__ import annotations

import subprocess  # nosec B404 - uso controlado
import sys
from pathlib import Path
from typing import Any

# Import ValueError explicitly to catch the specific package loader error
from jinja2 import Environment, PackageLoader, select_autoescape

from ...utils.config import ToolkitConfig

# --- FIX: Wrap Jinja initialization in try/except ---
# This prevents the CLI from crashing on import if templates are missing.
try:
    JINJA_ENV = Environment(
        loader=PackageLoader("toolkit.plugins.duplication_checker"),
        autoescape=select_autoescape(["html", "xml"]),
    )
except ValueError:
    # This happens if the 'templates' folder is not included in the package.
    # We set it to None so the plugin loads, but html generation will fallback.
    JINJA_ENV = None
# ----------------------------------------------------


class Plugin:
    def __init__(self) -> None:
        self.min_name_length = 10

    def configure(self, config: ToolkitConfig) -> None:
        """Recebe parâmetros de [plugins.duplication_checker] do toolkit.toml."""
        sect = getattr(getattr(config, "plugins", None), "duplication_checker", None)
        if not sect:
            return
        self.min_name_length = int(
            getattr(sect, "min_name_length", self.min_name_length)
        )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DuplicationChecker",
            "version": "0.1.0",
            "description": "Detects duplicated code using pylint R0801",
        }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def render_html(self, results) -> str:
        # --- FIX: Check if JINJA_ENV exists ---
        if JINJA_ENV is None:
            return "<html><body>Error: Templates not found (packaging issue).</body></html>"
            
        template = JINJA_ENV.get_template("dashboard.html")
        return template.render(results=results)

    def generate_dashboard(self, results):
        """
        Generates the D3.js dashboard HTML file.
        """
        dashboard_file = "src/toolkit/plugins/duplication_checker/"
        dashboard_file += "duplication_checker_dashboard.html"
        html_content = self.render_html(results)

        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    # ------------------------------------------------------------------
    # Analyze
    # ------------------------------------------------------------------

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
        proc = subprocess.run(  # nosec B603
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

        results = {
            "plugin": self.get_metadata()["name"],
            "results": results,
            "summary": summary,
        }

        return results