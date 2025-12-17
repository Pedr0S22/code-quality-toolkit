"""Plugin que procura por codigo duplicado."""

from __future__ import annotations

import json
from pathlib import Path

from ...utils.config import ToolkitConfig


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
    # Analyze
    # ------------------------------------------------------------------

    def render_html(self, results) -> str:
        # --- FIX: Check if JINJA_ENV exists ---
        if JINJA_ENV is None:
            return (
                "<html><body>Error: Templates not found "
                "(packaging issue).</body></html>"
            )

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

    def render_html(self, results) -> str:
        """
        Prepares data and returns the final HTML dashboard.
        """
        dashboard_data = self._aggregate_data_for_dashboard(results)
        data_json = json.dumps(dashboard_data)
        return self._get_html_template(data_json)

    def _aggregate_data_for_dashboard(self, results):
        """
        Aggregates duplication results into a dashboard-friendly structure.
        """
        rule_code = "DUPLICATED_CODE"

        file_counts = {}
        total_issues = 0

        # Unwrap results list if passed in the new format
        items = results.get("results", []) if isinstance(results, dict) else results

        for item in items:
            path = item.get("path") or item.get("file")
            if not path:
                continue
            file_counts[path] = file_counts.get(path, 0) + 1
            total_issues += 1

        top_files = [
            {
                "file": path,
                "count": count,
                "type": rule_code,
            }
            for path, count in sorted(
                file_counts.items(),
                key=lambda x: x[1],
                reverse=True)
        ][:10]

        return {
            "metrics": {
                "total_files": len(file_counts),
                "total_issues": total_issues,
            },
            "rule_counts": [
                {"code": rule_code, "count": total_issues}
            ],
            "top_files": top_files,
        }

        return results
