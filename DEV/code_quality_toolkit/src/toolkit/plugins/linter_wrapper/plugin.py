"""Lint wrapper plugin using pylint."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404
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
        """Analisa um único ficheiro com os linters configurados."""
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

            # ---------------------------
            # NEW: Generate dashboard here
            # ---------------------------
            from pathlib import Path
            plugin_dir = Path(__file__).parent

            self.generate_dashboard(
                {
                    "results": results,
                    "summary": {
                        "issues_found": len(results),
                        "highest_severity": highest_severity,
                        "issues_by_severity": issues_by_severity,
                    },
                    "files": [file_path] if file_path else [],
                },
                plugin_dir,
            )
            # ---------------------------

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
                            f"Linter '{linter}' não é suportado pelo " "LinterWrapper."
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
            sys.executable,
            "-m",
            "pylint",
            "--output-format=json",
            *extra_args,
            file_path,
        ]

        try:
            proc = subprocess.run(  # nosec B603
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
                    "message": "Python interpreter not found.",
                    "line": 1,
                    "col": 1,
                    "hint": "Check your python installation.",
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

        if proc.returncode != 0 and "No module named" in stderr and "pylint" in stderr:
            return [
                {
                    "severity": "high",
                    "code": "LINTER_NOT_FOUND",
                    "message": (
                        "O módulo 'pylint' não foi encontrado no ambiente Python atual."
                    ),
                    "line": 1,
                    "col": 1,
                    "hint": "Instale pylint (pip install pylint).",
                }
            ]

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
                str(msg.get("message-id", "")) or str(msg.get("symbol", "")) or "PYLINT"
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

    # ------------------------------------------------
    # NEW METHOD — D3.js Dashboard generator
    # ------------------------------------------------
    def generate_dashboard(self, results, output_dir):
        filename = "linterwrapper_dashboard.html"
        dashboard_file = os.path.join(output_dir, filename)

        data_json = json.dumps(results)

        html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>LinterWrapper Dashboard</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
    body {{ font-family: sans-serif; margin: 0; padding: 20px; }}
    .chart-container {{
        width: 1066px;
        height: 628px;
        border: 1px solid #ddd;
    }}
</style>
</head>
<body>
<h1>LinterWrapper Dashboard</h1>

<div class="chart-container" id="chart"></div>

<script>
const data = {{DATA_JSON}};
console.log("Dashboard data:", data);

// TODO: Add D3 visualization here
</script>

</body>
</html>
""".replace("{{DATA_JSON}}", data_json)

        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(html)
