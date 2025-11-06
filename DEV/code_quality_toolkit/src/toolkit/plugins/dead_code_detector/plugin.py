"""Dead code detector plugin"""

from __future__ import annotations

from typing import Any, Dict, List

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

class Plugin:
    """Plugin que deteta 'dead code'."""

    def __init__(self) -> None:
        pass

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""
        pass

    def get_metadata(self) -> Dict[str, str]:
        return {
            "name": "DeadCodeDetector",
            "version": "0.1.0",
            "description": "Deteta funções ou variáveis nunca usadas",
        }

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
        pass