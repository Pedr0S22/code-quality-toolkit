# ------------------------ #
#   Basic metrics plugin   #
# ------------------------ # 

from __future__ import annotations

import os
import tempfile
from typing import Any

from radon.raw import analyze as raw_analyze
from radon.metrics import h_visit, HalsteadReport
from ...utils.config import ToolkitConfig
from ...core.contracts import IssueResult

def issue():
    pass

class Plugin:
    """
    Basic Metrics Plugin
    """

    def __init__(self) -> None:
        self.report_level = 'LOW'

    def get_metadata(self) -> dict[str, str]:
        return {
                "name": "BasicMetrics",
                "version": "1.0.0",
                "description": "Reports basic code metrics like LOC, comments, and Halstead metrics.",
                }

    def configure(self, config: ToolkitConfig) -> None:
        if hasattr(config.rules, "metrics_report_level"):
            self.report_level = config.rules.metrics_report_level

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        try:
            results = []

            # ---- Raw metrics ----
            raw = raw_analyze(source_code)
            raw_metrics = {
                "total_lines": raw.loc,
                "logical_lines": raw.lloc,
                "comment_lines": raw.comments,
                "blank_lines": raw.blank,
                "docstrings": raw.multi,
            }

            for key, value in raw_metrics.items():
                res = {
                    "severity": "low",
                    "code": key,
                    "message": f"{key.replace('_',' ').title()}: {value}",
                    # "line": 0,
                    # "col": 0,
                    "hint": "",
                }

                # não esquecer que pode haver 0 linhas
                percent = value / raw_metrics["total_lines"] * 100 if raw_metrics["total_lines"] > 0 else 0

                # total_lines thresholds
                if key == "total_lines":
                    if value > 3000:
                        res["severity"] = "high"
                        res["hint"] = "File is larger than 3000 lines, consider splitting functionality across multiple files."
                    elif value > 2000:
                        res["severity"] = "medium"
                        res["hint"] = "File is larger than 2000 lines, consider splitting functionality across multiple files."
                    elif value > 1000:
                        res["hint"] = "File is larger than 1000 lines, consider splitting functionality across multiple files."
                    else:
                        continue

                # logical_lines
                elif key == "logical_lines":
                    if value > 300:
                        res["severity"] = "high"
                        res["hint"] = "Very large logical code blocks. Consider splitting into smaller functions."
                    elif value > 200:
                        res["severity"] = "medium"
                        res["hint"] = "Long logical blocks. Consider splitting into smaller functions."
                    elif value > 100:
                        res["hint"] = "Logical size is manageable but consider splitting into smaller functions."
                    else:
                        continue

                # comment_lines
                elif key == "comment_lines":
                    if percent < 2:
                        res["severity"] = "high"
                        res["hint"] = "Very few comments. Add documentation to improve readability."
                    elif percent < 5:
                        res["severity"] = "medium"
                        res["hint"] = "Low comment count, consider adding documentation."
                    elif percent < 10:
                        res["hint"] = "Consider adding documentation."
                    else:
                        continue

                # blank_lines
                elif key == "blank_lines":
                    if value < 1:
                        res["severity"] = "high"
                        res["hint"] = "No blank lines. Seriously?"
                    if percent < 5:
                        res["severity"] = "medium"
                        res["hint"] = "Very few blank lines. Consider adding spacing to improve readability."
                    if percent < 10:
                        res["hint"] = "Consider adding spacing to improve readability."
                    else:
                        continue

                # docstrings
                elif key == "docstrings":
                    if percent < 2:
                        res["severity"] = "high"
                        res["hint"] = "Very few docstrings. Add documentation for functions and classes."
                    elif percent < 4:
                        res["severity"] = "medium"
                        res["hint"] = "Low docstring count, consider adding documentation."
                    elif percent < 8:
                        res["hint"] = "Consider adding docstrings for functions and classes."
                    else:
                        continue

                results.append(res)

            return {
                    "results": results,
                    "summary": {
                        "issues_found": len(results),
                        "status": "completed",
                        },
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
