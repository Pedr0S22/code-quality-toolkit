"""
Real Integration Tests for Web App workflow.
ZIP Upload -> Server -> Core Analysis -> ZIP Response
and Web vs CLI equivalence (stable summary fields).
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from toolkit.core.cli import EXIT_SUCCESS
from toolkit.core.cli import main as cli_main
from web.server import app

fastapi = pytest.importorskip("fastapi")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_project_zip(tmp_path: Path) -> bytes:
    """
    Creates a project zip containing code that should:
      - trigger CyclomaticComplexity (nested ifs)
      - trigger DeadCodeDetector (unused function)
    """
    src = tmp_path / "src"
    src.mkdir()

    code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            return 1
        else:
            return 2
    else:
        return 3

def unused_function():
    pass
"""
    (src / "main.py").write_text(code, encoding="utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src / "main.py", arcname="main.py")
    return buf.getvalue()


def _extract_zip_bytes(content: bytes, out_dir: Path) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(out_dir)
        return zf.namelist()


def test_run_analysis_end_to_end_includes_reports_and_dashboards(
    client: TestClient, tmp_path: Path
):
    zip_bytes = _make_project_zip(tmp_path)

    configs = {
        "CyclomaticComplexity": {"enabled": True},
        "DeadCodeDetector": {"enabled": True},
        "analyze": {"include": ["**/*.py"], "exclude": []},
    }

    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("project.zip", zip_bytes, "application/zip")},
        data={"configs": json.dumps(configs)},
    )

    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "application/zip"

    out_dir = tmp_path / "web_out"
    out_dir.mkdir()
    names = _extract_zip_bytes(resp.content, out_dir)

    # Main outputs
    assert "report.json" in names
    assert "report.html" in names
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.html").exists()

    # Dashboards required by sprint
    assert "dead_code_detector_dashboard.html" in names
    assert "cyclomatic_complexity_dashboard.html" in names
    assert (out_dir / "dead_code_detector_dashboard.html").exists()
    assert (out_dir / "cyclomatic_complexity_dashboard.html").exists()

    # Basic sanity: report.json is valid
    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert "summary" in report


def test_web_output_matches_cli_summary_fields(client: TestClient, tmp_path: Path):
    """
    Compare Web report.json vs CLI report.json (stable fields only).
    """
    # --- Create same project directory for CLI ---
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "def complex(x):\n"
        "    if x > 0:\n"
        "        if x > 10:\n"
        "            return 1\n"
        "        return 2\n"
        "    return 3\n\n"
        "def unused_function():\n"
        "    pass\n",
        encoding="utf-8",
    )

    cli_out = tmp_path / "cli_report.json"

    exit_code = cli_main(
        [
            "analyze",
            str(project_dir),
            "--out",
            str(cli_out),
            "--plugins",
            "CyclomaticComplexity,DeadCodeDetector",
        ]
    )
    assert exit_code == EXIT_SUCCESS
    assert cli_out.exists()
    cli_report = json.loads(cli_out.read_text(encoding="utf-8"))

    # --- Now run Web with zip of same file ---
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(project_dir / "main.py", arcname="main.py")

    configs = {
        "CyclomaticComplexity": {"enabled": True},
        "DeadCodeDetector": {"enabled": True},
        "analyze": {"include": ["**/*.py"], "exclude": []},
    }

    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("upload.zip", zip_buf.getvalue(), "application/zip")},
        data={"configs": json.dumps(configs)},
    )
    assert resp.status_code == 200

    web_out_dir = tmp_path / "web_out"
    web_out_dir.mkdir()
    _extract_zip_bytes(resp.content, web_out_dir)
    web_report = json.loads((web_out_dir / "report.json").read_text(encoding="utf-8"))

    # Compare only stable summary fields (avoid brittle comparisons)
    assert cli_report["summary"]["total_files"] == web_report["summary"]["total_files"]

    if "issues" in cli_report["summary"] and "issues" in web_report["summary"]:
        assert cli_report["summary"]["issues"] == web_report["summary"]["issues"]
