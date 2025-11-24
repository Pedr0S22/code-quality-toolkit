"""Plugin que procura por codigo duplicado."""

from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class DuplicateCodeChecker:

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
        # Build signature map: signature -> list of starting line numbers
        sig_map: dict[int, list[int]] = {}
        blocks: dict[int, str] = {}
        for i in range(len(lines) - window + 1):
            block = "\n".join(lines[i : i + window])
            sig = hash(block)
            sig_map.setdefault(sig, []).append(i + 1)
            # store one block sample per signature
            if sig not in blocks:
                blocks[sig] = block

        # Convert to grouped results: one entry per signature that appears more than once
        groups: list[dict[str, Any]] = []
        for sig, locs in sig_map.items():
            if len(locs) > 1:
                groups.append({
                    "signature": sig,
                    "lines": locs,
                    "block": blocks.get(sig, ""),
                    "occurrences": len(locs),
                })

        return groups


dc = DuplicateCodeChecker()


class Plugin:
    def __init__(self) -> None:
        self.max_complexity = 10

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""
        self.max_line_length = config.rules.max_line_length

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DuplicationChecker",
            "version": "0.1.0",
            "description": "Plugin que procura por codigo duplicado.",
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        # Use grouped output from the checker (each group has signature, lines, block, occurrences)
        groups = dc.check(source_code)

        results: list[dict[str, Any]] = []
        for g in groups:
            line_numbers = g.get("lines", [])
            occurrences = g.get("occurrences", 1)
            block = g.get("block", "")
            signature = g.get("signature")

            # Heuristic similarity and suggestion
            similarity = min(100, 50 + occurrences * 10)
            refactoring_suggestion = "Extrair função" if occurrences > 2 else "Consolidar bloco"

            results.append({
                "plugin": self.get_metadata()["name"],
                "file": file_path or "unknown",
                "entity": "bloco duplicado",
                "line_numbers": line_numbers,
                "similarity": similarity,
                "refactoring_suggestion": refactoring_suggestion,
                "details": {
                    "occurrences": occurrences,
                    "message": block,
                },
                "metric": "duplicate_code",
                "value": None,
                "severity": "high" if occurrences > 2 else "medium",
                "code": "DUPLICATED_CODE",
                "message": block or f"Duplicate block (signature {signature})",
                "line": line_numbers[0] if line_numbers else 0,
                "col": 0,
                "hint": "Refactor to remove repeated logic.",
            })

        summary = {"issues_found": len(results), "status": "completed"}

        # summary entry for compatibility
        total_occurrences = sum(g.get("occurrences", 0) for g in groups)
        all_lines = [ln for g in groups for ln in g.get("lines", [])]
        summary_entry = {
            "plugin": self.get_metadata()["name"],
            "file": file_path or "unknown",
            "entity": "bloco duplicado",
            "line_numbers": all_lines,
            "details": {
                "occurrences": total_occurrences,
                "message": f"Found {total_occurrences} duplicated code blocks.",
            },
            "metric": "duplicate_code",
            "value": None,
            "severity": "high" if total_occurrences > 2 else "medium",
            "code": "DUPLICATED_CODE",
            "message": "Multiple duplicated code blocks found.",
            "line": all_lines[0] if all_lines else 0,
            "col": 0,
            "hint": "Consider refactoring to reduce code duplication.",
            "summary": summary,
        }

        results_with_summary = results + [summary_entry]

        return {
            "plugin": self.get_metadata()["name"],
            "results": results_with_summary,
            "summary": summary,
        }