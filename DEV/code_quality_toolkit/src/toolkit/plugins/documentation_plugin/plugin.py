"""Plugin that checks for missing docstrings in source code."""

from typing import Any, Dict, List
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

class Plugin:
    """DocumentationPlugin - verifies presence of module and function docstrings."""

    def __init__(self) -> None:
        self.check_docstrings = True

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin from toolkit rules (if provided)."""
        self.check_docstrings = getattr(config.rules, "check_docstrings", True)

    def get_metadata(self) -> Dict[str, str]:
        return {
            "name": "DocumentationPlugin",
            "version": "0.1.0",
            "description": "Checks for missing or incomplete docstrings in Python modules.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
        """Scan the code and report if it lacks proper documentation."""
        results: List[IssueResult] = []
        try:
            if self.check_docstrings:
                if '"""' not in source_code:
                    results.append({
                        "severity": "info",
                        "code": "MISSING_DOCSTRING",
                        "message": "Module or functions lack docstrings.",
                        "line": 1,
                        "col": 1,
                        "hint": "Add descriptive docstrings to improve documentation quality.",
                    })
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }
        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }
