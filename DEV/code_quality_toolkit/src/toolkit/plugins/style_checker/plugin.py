"""Simple style checking plugin."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

_SNAKE_CASE_RE = re.compile(r"^[a-z0-9_]+\.py$")
_TRAILING_WS_RE = re.compile(r"[ \t]+$")
_LEADING_WS_RE = re.compile(r"^([ \t]+)")

class Plugin:
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

    def get_metadata(self) -> Dict[str, str]:
        return {
            "name": "StyleChecker",
            "version": "0.1.2",
            "description": "Valida comprimento de linhas, convenções simples de nomes, trailingwhitespace e identation.",
        }
    
    def _check_trailing_whitespace(self, lines: List[str]) -> List[IssueResult]:
        results: List[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            m = _TRAILING_WS_RE.search(line)
            if m:
                col = m.start() + 1
                results.append(
                    {
                        "severity": "low",
                        "code": "TRAILING_WHITESPACE",
                        "message": "Espaços ou tabulações no final da linha.",
                        "line": idx,
                        "col": col,
                        "hint": "Remova os espaços/tabulações no final.",
                    }
                )
        return results

    def _check_indentation(self, lines: List[str]) -> List[IssueResult]:
        results: List[IssueResult] = []
        for idx, line in enumerate(lines, start=1):
            if not line:  
                continue

            m = _LEADING_WS_RE.match(line)
            if not m:
                continue  

            leading = m.group(1)  
            has_tab = "\t" in leading
            has_space = " " in leading

            if has_tab and has_space and not self.allow_mixed_indentation:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_MIXED",
                        "message": "Mistura de tabulações e espaços no início da linha.",
                        "line": idx,
                        "col": 1,
                        "hint": "Utilize apenas um estilo: defina o ficheiro rules.indent_style e ajuste o seu editor.",
                    }
                )

            if self.indent_style == "spaces" and has_tab:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_TABS_NOT_ALLOWED",
                        "message": "Os recuos com tabulações não são permitidos (os espaços são obrigatórios).",
                        "line": idx,
                        "col": 1,
                        "hint": f"Converter tabulações em espaços (múltiplos de {self.indent_size}).",
                    }
                )

                continue

            if self.indent_style == "tabs" and has_space:
                results.append(
                    {
                        "severity": "low",
                        "code": "INDENT_SPACES_NOT_ALLOWED",
                        "message": "Não são permitidos recuos com espaços (tabulações são obrigatórias).",
                        "line": idx,
                        "col": 1,
                        "hint": "Converter espaços em tabulações para criar avanços.",
                    }
                )
                continue

            if self.indent_style == "spaces" and has_space and not has_tab:
                width = len(leading)  
                if width % self.indent_size != 0:
                    results.append(
                        {
                            "severity": "low",
                            "code": "INDENT_WIDTH",
                            "message": f"O recuo não é um múltiplo de espaços {self.indent_size}.",
                            "line": idx,
                            "col": 1,
                            "hint": f"Ajuste o recuo para múltiplos de {self.indent_size}.",
                        }
                    )

        return results

    def analyze(self, source_code: str, file_path: str | None) -> Dict[str, Any]:
        results: List[IssueResult] = []
        lines = source_code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line) > self.max_line_length:
                results.append(
                    {
                        "severity": "low",
                        "code": "LINE_LENGTH",
                        "message": f"Linha com {len(line)} caracteres",
                        "line": idx,
                        "col": 1,
                        "hint": f"Máximo configurado: {self.max_line_length}",
                    }
                )
        
        if self.check_whitespace:
            results.extend(self._check_trailing_whitespace(lines))

        results.extend(self._check_indentation(lines))
        
        if file_path and not _SNAKE_CASE_RE.match(Path(file_path).name):
            results.append(
                {
                    "severity": "info",
                    "code": "FILENAME_STYLE",
                    "message": "Nome do ficheiro não segue snake_case.",
                    "line": 1,
                    "col": 1,
                    "hint": "Utilize nomes como sample_module.py",
                }
            )
        return {
            "results": results,
            "summary": {
                "issues_found": len(results),
                "status": "completed",
            },
        }
# EXTENSION-POINT: adicionar novas regras, p.ex. indentação ou trailing whitespace.
