"""Plugin base protocol and helper utilities."""

from __future__ import annotations

from typing import Any, Dict, Protocol

from ..core.contracts import PluginMetadata


class BasePlugin(Protocol):
    """Protocol that plugin implementations must follow."""

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata including name, version and description."""

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
        """Execute the analysis and return a plugin report."""


# EXTENSION-POINT: adicionar classes utilitárias partilhadas por múltiplos plugins aqui.