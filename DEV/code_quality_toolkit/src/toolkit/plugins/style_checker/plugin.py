"""Simple style checking plugin."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Importar os tipos CORRIGIDOS do Contrato
from ...core.contracts import (
    PluginProtocol,
    PluginExecutionResult,
    PluginMetadata,
    IssueResult,
)
from ...utils.config import ToolkitConfig 

_SNAKE_CASE_RE = re.compile(r"^[a-z0-9_]+\.py$")
_TRAILING_WS_RE = re.compile(r"[ \t]+$")
_LEADING_WS_RE = re.compile(r"^([ \t]+)")

# CORREÇÃO: O nome da classe DEVE ser 'Plugin' para o loader encontrar
class Plugin(PluginProtocol): 
    """Plugin que valida regras de estilo básicas."""

    def __init__(self) -> None:
        self.max_line_length = 88
        self.check_whitespace = True
        self.indent_style = "spaces" 
        self.indent_size = 4
        self.allow_mixed_indentation = False

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""
        self.max_line_length = config.rules.max_line_length
        self.check_whitespace = config.rules.check_whitespace
        self.indent_style = config.rules.indent_style
        self.indent_size = config.rules.indent_size
        self.allow_mixed_indentation = config.rules.allow_mixed_indentation

    def get_metadata(self) -> PluginMetadata:
        """Implementa o método do contrato."""
        return {
            "name": "StyleChecker",
            "version": "0.1.2",
            "author": "Equipa Style",
            "description": "Valida comprimento de linhas, convenções simples de nomes, trailing whitespace e identation.",
        }

    # Funções auxiliares (refatoradas para o Contrato)
    def _check_trailing_whitespace(self, lines: List[str], file: str) -> List[IssueResult]:
        results: List[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            m = _TRAILING_WS_RE.search(line)
            if m:
                col = m.start() + 1
                results.append(
                    {
                        "file": file,
                        "entity": f"Linha {idx}",
                        "line": idx,
                        "metric": "TRAILING_WHITESPACE",
                        "value": m.group(0), 
                        "severity": "low",
                        "message": "Espaços ou tabulações no final da linha.",
                        "col": col,
                        "hint": "Remova os espaços/tabulações no final.",
                    }
                )
        return results

    def _check_indentation(self, lines: List[str], file: str) -> List[IssueResult]:
        results: List[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            if not line: continue
            m = _LEADING_WS_RE.match(line)
            if not m: continue  

            leading = m.group(1)  
            has_tab = "\t" in leading
            has_space = " " in leading

            common_finding = {
                "file": file,
                "entity": f"Linha {idx}",
                "line": idx,
                "value": leading,
                "severity": "low",
                "col": 1,
            }

            if has_tab and has_space and not self.allow_mixed_indentation:
                results.append(
                    {
                        **common_finding,
                        "metric": "INDENT_MIXED",
                        "message": "Mistura de tabulações e espaços no início da linha.",
                        "hint": "Utilize apenas um estilo: defina o ficheiro rules.indent_style e ajuste o seu editor.",
                    }
                )

            if self.indent_style == "spaces" and has_tab:
                results.append(
                    {
                        **common_finding,
                        "metric": "INDENT_TABS_NOT_ALLOWED",
                        "message": "Os recuos com tabulações não são permitidos (os espaços são obrigatórios).",
                        "hint": f"Converter tabulações em espaços (múltiplos de {self.indent_size}).",
                    }
                )
                continue

            if self.indent_style == "tabs" and has_space:
                results.append(
                    {
                        **common_finding,
                        "metric": "INDENT_SPACES_NOT_ALLOWED",
                        "message": "Não são permitidos recuos com espaços (tabulações são obrigatórias).",
                        "hint": "Converter espaços em tabulações para criar avanços.",
                    }
                )
                continue

            if self.indent_style == "spaces" and has_space and not has_tab:
                width = len(leading)  
                if width % self.indent_size != 0:
                    results.append(
                        {
                            **common_finding,
                            "metric": "INDENT_WIDTH",
                            "message": f"O recuo não é um múltiplo de espaços {self.indent_size}.",
                            "hint": f"Ajuste o recuo para múltiplos de {self.indent_size}.",
                        }
                    )
        return results

    def analyze(self, source_code: str, file_path: Optional[str]) -> PluginExecutionResult:
        """Implementa o método de análise."""
        
        findings: List[IssueResult] = []
        lines = source_code.splitlines()
        current_file = file_path or "<input>"

        # 1. Análise de Comprimento de Linha
        for idx, line in enumerate(lines, start=1):
            line_len = len(line)
            if line_len > self.max_line_length:
                finding: IssueResult = {
                    "file": current_file,
                    "entity": f"Linha {idx}",
                    "line": idx,
                    "metric": "LINE_LENGTH",
                    "value": line_len,
                    "severity": "low",
                    "message": f"Linha com {line_len} chars (Max: {self.max_line_length}).",
                }
                findings.append(finding)

        # 2. Análise de Whitespace
        if self.check_whitespace:
            findings.extend(self._check_trailing_whitespace(lines, current_file))

        # 3. Análise de Indentação
        findings.extend(self._check_indentation(lines, current_file))
        
        # 4. Análise de Nome de Ficheiro
        if file_path and not _SNAKE_CASE_RE.match(Path(file_path).name):
            finding: IssueResult = {
                "file": current_file,
                "entity": "Ficheiro",
                "line": 1,
                "metric": "FILENAME_STYLE",
                "value": Path(file_path).name,
                "severity": "info",
                "message": "Nome do ficheiro não segue a convenção snake_case.",
            }
            findings.append(finding)

        # O retorno DEVE incluir a chave 'plugin'
        return {
            "plugin": self.get_metadata(),
            "results": findings,
            "summary": {
                "issues_found": len(findings),
                "status": "completed",
            },
        }