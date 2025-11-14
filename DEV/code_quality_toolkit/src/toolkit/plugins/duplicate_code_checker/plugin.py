"""Plugin que procura por codigo duplicado."""

from typing import Any, Dict, List

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

class _DuplicateCodeChecker:

    def normalize(self, data: str):
        out = []
        for line in data.splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                out.append(clean)
        return out

    def check(self, src: str, window: int = 3):
        self.src = src
        lines = self.normalize(src)

        sig_map = {}
        for i in range(len(lines) - window + 1):
            block = "\n".join(lines[i:i + window])
            sig = hash(block)
            sig_map.setdefault(sig, []).append(i + 1)

        duplicates = []
        for sig, locs in sig_map.items():
            if len(locs) > 1:
                for line in locs:
                    res = {
                        "severity": "medium",
                        "code": "DUPLICATED_CODE",
                        "message": f"Duplicate block (signature {sig})",
                        "line": line,
                        "col": 0,
                        "hint": "Refactor to remove repeated logic.",
                    }
                    duplicates.append(res)
        return duplicates

dc = _DuplicateCodeChecker()

class Plugin:
    def __init__(self) -> None:
        self.max_complexity = 10

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""
        self.max_line_length = config.rules.max_line_length

    def get_metadata(self) -> Dict[str, str]:
        return {
            "name": "DuplicationChecker",
            "version": "0.1.0",
            "description": "Plugin que procura por codigo duplicado.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
        dup = dc.check(source_code)
        results: List[IssueResult] = [ x for x in dup ]
        return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                    },
                }

