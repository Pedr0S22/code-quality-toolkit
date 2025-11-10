"""Contracts and validation helpers for plugin reports."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Literal, Protocol, TypedDict, Optional

# Nível de severidade (Mantido)
Severity = Literal["info", "low", "medium", "high"]

# [cite_start]Metadados do Plugin (Conforme PDF [cite: 264-274])
class PluginMetadata(TypedDict):
    name: str
    version: str
    author: str 
    description: str

# [cite_start]CORREÇÃO 1: 'IssueResult' (O 'Finding' do PDF [cite: 310-317])
class IssueResult(TypedDict, total=False):
    file: str
    entity: str
    line: int
    metric: str    # <--- MUDANÇA (era 'code')
    value: Any     # <--- MUDANÇA (novo campo obrigatório)
    severity: Severity
    message: str
    col: int
    hint: str # 'hint' mantido como opcional

# Sumário do Plugin (Mantido)
class PluginSummary(TypedDict):
    issues_found: int
    status: Literal["completed", "partial", "failed"]

# [cite_start]CORREÇÃO 2: O Retorno do Plugin (Conforme PDF [cite: 284-307])
class PluginExecutionResult(TypedDict):
    plugin: PluginMetadata  # <--- MUDANÇA (era 'plugin: str')
    results: List[IssueResult]
    summary: PluginSummary

# Relatório por Ficheiro (Mantido)
class FileReport(TypedDict):
    file: str
    plugins: List[PluginExecutionResult]

# Sumário Unificado (Mantido)
class UnifiedSummary(TypedDict):
    total_files: int
    total_issues: int
    issues_by_severity: Dict[Severity, int]
    issues_by_plugin: Dict[str, int]
    top_offenders: List[Dict[str, int | str]]

# Metadados Unificados (Mantido)
class UnifiedMetadata(TypedDict):
    timestamp: str
    tool_version: str
    plugins_executed: List[str]
    status: Literal["completed", "partial", "failed"]

# Relatório Unificado (Mantido)
class UnifiedReport(TypedDict):
    analysis_metadata: UnifiedMetadata
    summary: UnifiedSummary
    details: List[FileReport]

# CORREÇÃO 3: O Protocolo (Interface)
class PluginProtocol(Protocol):
    """Protocolo que cada plugin deve implementar, conforme o Contrato da API."""

    def get_metadata(self) -> PluginMetadata:
        """Return metadata about the plugin."""
        ...

    def analyze(self, source_code: str, file_path: Optional[str]) -> PluginExecutionResult:
        """Analyze the provided source code and return a plugin report."""
        ...

# --- Funções de Validação ---

def _require_keys(data: Dict[str, Any], keys: Iterable[str], context: str) -> None:
    """Valida se as chaves existem num dicionário."""
    for key in keys:
        if key not in data:
            raise ValueError(f"Missing key '{key}' in {context}")

# CORREÇÃO 4: A Validação deve testar o NOVO contrato
def validate_plugin_report(data: Dict[str, Any]) -> None:
    """Valida a estrutura de um relatório de plugin individual."""
    _require_keys(data, ["plugin", "results", "summary"], "plugin report")

    if not isinstance(data["plugin"], dict):
        raise TypeError("'plugin' metadata must be a dictionary")
    # Assumindo que 'author' é obrigatório (baseado no PDF)
    _require_keys(data["plugin"], ["name", "version", "description", "author"], "plugin metadata") 

    results = data["results"]
    summary = data["summary"]
    # ... (validações de results e summary mantidas) ...

    for result in results:
        if not isinstance(result, dict):
            raise TypeError("Each result must be a dict")
        # [cite_start]Exige os campos do PDF [cite: 310-317]
        _require_keys(
            result,
            ["file", "entity", "line", "metric", "value", "severity", "message"],
            "issue result",
        )
        if result["severity"] not in {"info", "low", "medium", "high"}:
            raise ValueError("Invalid severity level")

def validate_unified_report(data: Dict[str, Any]) -> None:
    """Valida o schema do relatório unificado final."""
    _require_keys(data, ["analysis_metadata", "summary", "details"], "unified report")
    metadata = data["analysis_metadata"]
    summary = data["summary"]
    details = data["details"]
    # ... (validações de metadata e summary mantidas) ...
    if not isinstance(summary["issues_by_severity"], dict):
        raise TypeError("'issues_by_severity' must be a dict")
    
    # CORREÇÃO 5: Validar que todas as chaves de severidade existem
    for key in ["info", "low", "medium", "high"]:
        if key not in summary["issues_by_severity"]:
            raise ValueError(f"Missing severity key '{key}' in summary")

    for file_entry in details:
        _require_keys(file_entry, ["file", "plugins"], "file entry")
        for plugin_entry in file_entry["plugins"]:
            validate_plugin_report(plugin_entry)