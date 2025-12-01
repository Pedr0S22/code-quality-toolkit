"""Lint wrapper plugin using pylint."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - usamos subprocess apenas para invocar 'pylint' localmente com argumentos controlados
import sys
import tempfile
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

_PYLINT_TYPE_TO_SEVERITY = {
    "convention": "low",
    "refactor": "low",
    "warning": "medium",
    "error": "high",
    "fatal": "high",
}

class Plugin:
    """Plugin que envuelve linters externos (inicialmente pylint)."""

    def __init__(self) -> None:
        self.enabled: bool = True
        self.enabled_linters: list[str] = ["pylint"]
        self.timeout_seconds: int = 60
        self.max_issues: int = 500
        self.pylint_args: list[str] = []
        self.fail_on_severity: str = "high"

    def configure(self, config: ToolkitConfig) -> None:
        """Configure o plugin a partir do ToolkitConfig."""
        lw = getattr(config, "linter_wrapper", None)

        if lw is not None:
            self.enabled = getattr(lw, "enabled", self.enabled)
            self.enabled_linters = list(getattr(lw, "linters", self.enabled_linters))
            self.timeout_seconds = int(
                getattr(lw, "timeout_seconds", self.timeout_seconds)
            )
            self.max_issues = int(getattr(lw, "max_issues", self.max_issues))
            self.pylint_args = list(getattr(lw, "pylint_args", self.pylint_args))
            self.fail_on_severity = str(
                getattr(lw, "fail_on_severity", self.fail_on_severity)
            )

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "LinterWrapper",
            "version": "0.1.0",
            "description": (
                "Executa linters externos (como pylint) e normaliza os resultados "
                "para o relatório do toolkit."
            ),
        }

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Analisa um único ficheiro com os linters configurados.

        Se não houver file_path, o código fonte é escrito para um ficheiro
        temporário .py para que o pylint possa ser executado.
        """
        try:
            if not self.enabled:
                return {
                    "results": [],
                    "summary": {
                        "issues_found": 0,
                        "status": "completed",
                        "highest_severity": None,
                        "issues_by_severity": {},
                        "fail_build": False,
                    },
                }

            temp_path: str | None = None
            if file_path:
                target_path = file_path
            else:
                fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
                os.close(fd)
                with open(temp_path, "w", encoding="utf-8") as tmp:
                    tmp.write(source_code)
                target_path = temp_path

            try:
                results, highest_severity = self._run_linters_on_file(target_path)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

            issues_by_severity: dict[str, int] = {}
            for issue in results:
                sev = issue.get("severity", "low")
                issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

            fail_build = self._should_fail_build(highest_severity)

            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                    "highest_severity": highest_severity,
                    "issues_by_severity": issues_by_severity,
                    "fail_build": fail_build,
                },
            }

        except Exception as exc:
            # Igual que StyleChecker: nunca crash, siempre responde algo
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(exc),
                },
            }

    def _run_linters_on_file(
        self,
        file_path: str,
    ) -> tuple[list[IssueResult], str | None]:
        """Executa todos os linters configurados num único ficheiro."""
        all_results: list[IssueResult] = []
        highest_severity: str | None = None
        order = {"low": 0, "medium": 1, "high": 2}

        for linter in self.enabled_linters:
            if linter == "pylint":
                lint_results = self._run_pylint(file_path)
            else:
                lint_results = [
                    {
                        "severity": "medium",
                        "code": "LINTER_UNSUPPORTED",
                        "message": (
                            f"Linter '{linter}' não é suportado pelo "
                            "LinterWrapper."
                        ),
                        "line": 1,
                        "col": 1,
                        "hint": (
                            "Remover o linter não suportado da configuração "
                            "ou implementar suporte."
                        ),
                    }
                ]

            all_results.extend(lint_results)

            for issue in lint_results:
                sev = issue.get("severity", "low")
                val = order.get(sev, -1)
                cur = order.get(highest_severity, -1) if highest_severity else -1
                if val > cur:
                    highest_severity = sev

            if len(all_results) >= self.max_issues:
                all_results = all_results[: self.max_issues]
                break

        return all_results, highest_severity

    def _run_pylint(self, file_path: str) -> list[IssueResult]:
        """Executa pylint no ficheiro dado e converte a saída JSON em IssueResult."""
        timeout_seconds = self.timeout_seconds
        extra_args = list(self.pylint_args)

        cmd: list[str] = [
            sys.executable,  # Points to .venv/bin/python or .venv/Scripts/python.exe
            "-m",
            "pylint",
            "--output-format=json",
            *extra_args,
            file_path,
        ]

        try:
            proc = subprocess.run( # nosec B603 - comando 'pylint' com lista de argumentos controlados, sem shell=True nem input do utilizador
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_NOT_FOUND",
                    "message": (
                        "Não foi possível executar 'pylint'. "
                        "Verifique se está instalado e disponível no PATH."
                    ),
                    "line": 1,
                    "col": 1,
                    "hint": "Instale pylint (por exemplo, 'pip install pylint').",
                }
            ]
        except subprocess.TimeoutExpired:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_TIMEOUT",
                    "message": (
                        f"'pylint' não terminou dentro de {timeout_seconds} segundos."
                    ),
                    "line": 1,
                    "col": 1,
                    "hint": (
                        "Simplifique o ficheiro ou aumente o timeout "
                        "em [plugins.linter_wrapper]."
                    ),
                }
            ]

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if not stdout:
            if proc.returncode != 0:
                return [
                    {
                        "severity": "high",
                        "code": "LINTER_ERROR",
                        "message": (
                            "pylint terminou com erro e não produziu saída JSON."
                        ),
                        "line": 1,
                        "col": 1,
                        "hint": f"Verifique a saída de erro: {stderr or 'sem stderr'}.",
                    }
                ]
            return []

        try:
            messages = json.loads(stdout)
        except json.JSONDecodeError:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_OUTPUT_INVALID",
                    "message": (
                        "pylint produziu uma saída que não pôde ser interpretada "
                        "como JSON."
                    ),
                    "line": 1,
                    "col": 1,
                    "hint": (
                        "Verifique se existem plugins/customizações de pylint que "
                        "alterem a saída."
                    ),
                }
            ]

        results: list[IssueResult] = []

        for msg in messages:
            msg_type = str(msg.get("type", "") or "")
            severity = _PYLINT_TYPE_TO_SEVERITY.get(msg_type, "low")

            line = int(msg.get("line", 0) or 0)
            col = int(msg.get("column", 0) or 0)
            msg_id = (
                str(msg.get("message-id", ""))
                or str(msg.get("symbol", ""))
                or "PYLINT"
            )
            text = str(msg.get("message", "")) or ""

            results.append(
                {
                    "severity": severity,
                    "code": msg_id,
                    "message": text,
                    "line": line,
                    "col": col,
                    "hint": (
                        f"Reveja a regra do pylint '{msg_id}' e ajuste o código "
                        "ou a configuração."
                    ),
                }
            )

            if len(results) >= self.max_issues:
                break

        return results

    def _should_fail_build(self, highest_severity: str | None) -> bool:
        if not highest_severity:
            return False
        if self.fail_on_severity == "none":
            return False

        order = {"low": 0, "medium": 1, "high": 2}
        threshold = order.get(self.fail_on_severity, 2)
        max_seen = order.get(highest_severity, -1)
        return max_seen >= threshold
