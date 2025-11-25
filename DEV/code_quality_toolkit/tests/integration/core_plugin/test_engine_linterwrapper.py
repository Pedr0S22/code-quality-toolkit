import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_engine_runs_linterwrapper_successfully(tmp_path):
    """
    Integration Test A: Engine + LinterWrapper (Pylint) integration.
    - Core debe cargar LinterWrapper desde toolkit.toml
    - Ejecutar análisis sobre un archivo Python
    - Recibir issues del plugin
    - Generar un reporte JSON con resultados de LinterWrapper
    """

    # ─────────────────────────────────────────────
    # 1. Crear proyecto temporal con archivo Python
    # ─────────────────────────────────────────────
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    sample_file = project_dir / "example.py"
    write_file(
        sample_file,
        "def bad_function():\n    a=1\n    return a\n"
    )

    # ─────────────────────────────────────────────
    # 2. Crear toolkit.toml con LintWrapper activado
    # ─────────────────────────────────────────────
    config_file = project_dir / "toolkit.toml"
    write_file(
        config_file,
        """
[plugins.LinterWrapper]
enabled = true
pylint_args = ["--disable=C0114"]    # disable 'missing module docstring'
fail_on_severity = "high"
"""
    )

    # ─────────────────────────────────────────────
    # 3. Ejecutar CLI sobre el proyecto
    # ─────────────────────────────────────────────
    report_path = project_dir / "report.json"

    cmd = [
        sys.executable,
        "-m", "toolkit.core.cli",
        "analyze",
        str(project_dir),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]


    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False
    )

    # Debug (si falla)
    print("\nSTDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # CLI must NOT crash
    assert result.returncode == 0, "CLI crashed when running LinterWrapper"

    # ─────────────────────────────────────────────
    # 4. Validar que el reporte JSON existe y es válido
    # ─────────────────────────────────────────────
    assert report_path.exists(), "Report file was not created"

    report = json.loads(report_path.read_text())

    # ─────────────────────────────────────────────
    # 5. Validar estructura del reporte unificado
    # ─────────────────────────────────────────────

    # Plugin debe aparecer como ejecutado
    assert "plugins_executed" in report["analysis_metadata"]
    assert "LinterWrapper" in report["analysis_metadata"]["plugins_executed"]

    # Debe haber una sección 'details'
    assert "details" in report
    assert isinstance(report["details"], list)

    # Debe haber issues reportados por LintWrapper
    lint_issues = [
        issue for issue in report["details"]
        if issue.get("plugin") == "LinterWrapper"
    ]
    assert len(lint_issues) > 0, "LinterWrapper returned no issues"

    # Los issues deben tener campos obligatorios
    first = lint_issues[0]
    assert "file" in first
    assert "metric" in first
    assert "severity" in first
    assert "message" in first
