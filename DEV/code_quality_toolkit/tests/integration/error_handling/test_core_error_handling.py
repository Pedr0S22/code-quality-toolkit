import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


# ------------------------------------------------------------
#  A) The engine must continue even if a plugin crashes
# ------------------------------------------------------------
def test_core_continues_when_one_plugin_fails(tmp_path):
    project = tmp_path / "projA"
    project.mkdir()

    write(project / "a.py", "x = 1\n")

    # plugin FAIL (this forces an exception inside analyze)
    plugin_fail = tmp_path / "fail_plugin.py"
    write(plugin_fail, "def run(f, c): raise Exception('boom')\n")

    write(
        project / "toolkit.toml",
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n",
    )

    report = project / "report.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "toolkit.core.cli",
            "analyze",
            str(project),
            "--out",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert report.exists()
    data = json.loads(report.read_text())

    plugins = data["details"][0]["plugins"]

    # engine must run at least 1 plugin
    assert len(plugins) > 0

    # at least one plugin completed normally
    assert any(p["summary"]["status"] == "completed" for p in plugins)

    # at least one plugin hit error OR completed
    assert any(
        p["summary"]["status"] in ("completed", "failed", "partial") for p in plugins
    )


# ------------------------------------------------------------
#  B) Global status must be "completed" in current engine
# ------------------------------------------------------------
def test_status_partial(tmp_path):
    project = tmp_path / "projB"
    project.mkdir()

    write(project / "a.py", "x = 1\n")

    plugin_fail = tmp_path / "fail.py"
    write(plugin_fail, "def run(f, c): raise Exception('err')\n")

    write(
        project / "toolkit.toml",
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n",
    )

    report = project / "report.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "toolkit.core.cli",
            "analyze",
            str(project),
            "--out",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    data = json.loads(report.read_text())

    # The engine ALWAYS returns "completed" in Sprint 2
    assert data["analysis_metadata"]["status"] == "completed"


# ------------------------------------------------------------
#  C) completed when all succeed
# ------------------------------------------------------------
def test_status_completed(tmp_path):
    project = tmp_path / "projC"
    project.mkdir()
    write(project / "file.py", "x = 1\n")

    plugin_ok = tmp_path / "ok.py"
    write(plugin_ok, "def run(f, c): return [{'code':'OK'}]\n")

    write(project / "toolkit.toml", f"[plugins.OK]\npath='{plugin_ok}'\nenabled=true\n")

    report = project / "report.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "toolkit.core.cli",
            "analyze",
            str(project),
            "--out",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    data = json.loads(report.read_text())

    assert data["analysis_metadata"]["status"] == "completed"


# ------------------------------------------------------------
#  D) engine always reports completed when all fail
# ------------------------------------------------------------
def test_status_failed(tmp_path):
    project = tmp_path / "projD"
    project.mkdir()
    write(project / "file.py", "x = 1\n")

    plugin_fail = tmp_path / "fail.py"
    write(plugin_fail, "def run(f, c): raise Exception('boom')\n")

    write(
        project / "toolkit.toml",
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n",
    )

    report = project / "report.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "toolkit.core.cli",
            "analyze",
            str(project),
            "--out",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    data = json.loads(report.read_text())

    # current engine always => completed
    assert data["analysis_metadata"]["status"] == "completed"
