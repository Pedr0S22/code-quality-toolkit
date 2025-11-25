import json
import os
import subprocess
import sys
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

    # 1) Crear proyecto temporal **dentro del repositorio**
    project_dir = ROOT / "_tmp_project"
    project_dir.mkdir(exist_ok=True)

    sample_file = project_dir / "example.py"
    write_file(
        sample_file,
        "def bad_function():\n    a=1\n    return a\n"
    )

    # 2) Crear toolkit.toml
    config_file = project_dir / "toolkit.toml"
    write_file(
        config_file,
        "[plugins.linter_wrapper]\n"
        "enabled = true\n"
        'pylint_args = ["--disable=C0114"]\n'
        'fail_on_severity = "high"\n'
    )


    # 3) Ejecutar CLI
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

    # Debe haber issues reportados por LinterWrapper
    lint_issues = []
    for det in report["details"]:
        for plug in det["plugins"]:
            if plug["plugin"] == "LinterWrapper":
                lint_issues.append(plug)

    assert len(lint_issues) > 0, "LinterWrapper returned no issues"


    # Los issues deben tener campos obligatorios
    first = lint_issues[0]
    assert "file" in first
    assert "metric" in first
    assert "severity" in first
    assert "message" in first

# ─────────────────────────────────────────────
# B1 — pylint missing
# ─────────────────────────────────────────────

def test_linterwrapper_handles_missing_pylint(tmp_path):
    """If pylint is not installed, LinterWrapper must return LINTER_NOT_FOUND."""

    project = tmp_path / "projB1"
    project.mkdir()

    sample_file = project / "a.py"
    write_file(sample_file, "x = 1\n")

    config_file = project / "toolkit.toml"
    write_file(
        config_file,
        "[plugins.linter_wrapper]\n"
        "enabled = true\n"
    )

    report_path = project / "report.json"

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

    report = json.loads(report_path.read_text())

    issues = []
    for det in report["details"]:
        for plug in det["plugins"]:
            if plug["plugin"] == "LinterWrapper":
                issues.append(plug)


    assert len(issues) > 0
    first = issues[0]["results"][0]
    assert first["code"] == "LINTER_NOT_FOUND"


# ─────────────────────────────────────────────
# B2 — timeout
# ─────────────────────────────────────────────
def test_linterwrapper_timeout(tmp_path):
    """LinterWrapper must return LINTER_TIMEOUT when pylint exceeds timeout."""

    project = tmp_path / "projB2"
    project.mkdir()

    sample = project / "slow.py"
    write_file(sample, "a = 1\n")

    config_file = project / "toolkit.toml"
    write_file(
        config_file,
        "[plugins.linter_wrapper]\n"
        "enabled = true\n"
        "timeout_seconds = 0\n"
    )

    report_path = project / "report.json"

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

    report = json.loads(report_path.read_text())

    issues = []
    for det in report["details"]:
        for plug in det["plugins"]:
            if plug["plugin"] == "LinterWrapper":
                issues.append(plug)


    assert len(issues) > 0
    first = issues[0]["results"][0]
    assert first["code"] == "LINTER_TIMEOUT"


# ─────────────────────────────────────────────
# B3 — invalid output
# ─────────────────────────────────────────────
def test_linterwrapper_invalid_json_output(tmp_path):
    """
    LinterWrapper must return LINTER_OUTPUT_INVALID when pylint returns
    invalid JSON.
    """


    project = tmp_path / "projB3"
    project.mkdir()

    # create python file
    write_file(project / "bad.py", "a=1\n")

    # create fake pylint that outputs random text
    fake_pylint = tmp_path / "pylint"
    fake_pylint.write_text("#!/bin/sh\necho not_json_output\n")
    fake_pylint.chmod(0o755)

    # force PATH to use fake pylint
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"

    write_file(
        project / "toolkit.toml",
        "[plugins.linter_wrapper]\n"
        "enabled = true\n"
    )

    report_path = project / "report.json"

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)

    report = json.loads(report_path.read_text())

    issues = []
    for det in report["details"]:
        for plug in det["plugins"]:
            if plug["plugin"] == "LinterWrapper":
                issues.append(plug)


    assert len(issues) > 0
    first = issues[0]["results"][0]
    assert first["code"] == "LINTER_OUTPUT_INVALID"

def test_linterwrapper_fail_on_severity_high(tmp_path):
    """
    C) El CLI debe devolver exit code 3 (EXIT_SEVERITY_ERROR)
    si LinterWrapper encuentra un issue de severidad >= high.
    """

    project = tmp_path / "projC"
    project.mkdir()

    # archivo python
    write_file(project / "file.py", "a=1\n")

    # activar LinterWrapper sin tocar severidad interna
    write_file(
        project / "toolkit.toml",
        "[plugins.linter_wrapper]\n"
        "enabled = true\n"
    )

    report_path = project / "report.json"

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
        "--fail-on-severity=high",
    ]

    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False    # important: NO lanzar excepción en exit code != 0
    )

    # debe devolver exit code 3
    assert result.returncode == 3, (
        f"CLI should fail with exit code 3, got {result.returncode}\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )

    # el reporte debe existir
    assert report_path.exists(), (
    "Missing report.json when fail_on_severity was triggered."
    )


    # y tener issues del plugin
    report = json.loads(report_path.read_text())
    linter_issues = []
    for det in report["details"]:
        for plug in det["plugins"]:
            if plug["plugin"] == "LinterWrapper":
                linter_issues.append(plug)

    assert len(linter_issues) > 0

