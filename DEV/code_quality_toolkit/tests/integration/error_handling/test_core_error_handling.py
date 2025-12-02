import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


# ------------------------------------------------------------
#  A) The engine must continue when one plugin crashes
# ------------------------------------------------------------
def test_core_continues_when_one_plugin_fails(tmp_path):
    project = tmp_path / "projA"
    project.mkdir()

    write(project / "a.py", "x = 1\n")

    plugin_ok = tmp_path / "ok_plugin.py"
    write(
        plugin_ok,
        "def run(filepath, config):\n"
        "    return [{'code': 'OK', 'message': 'ok', 'severity': 'low'}]\n"
    )

    plugin_fail = tmp_path / "fail_plugin.py"
    write(
        plugin_fail,
        "def run(filepath, config):\n"
        "    raise Exception('boom')\n"
    )

    write(
        project / "toolkit.toml",
        f"[plugins.OK]\npath='{plugin_ok}'\nenabled=true\n"
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n"
    )

    report = project / "report.json"

    subprocess.run(
        [sys.executable, "-m", "toolkit.core.cli", "analyze",
         str(project), "--out", str(report)],
        cwd=ROOT, text=True, capture_output=True, check=False
    )

    assert report.exists()
    data = json.loads(report.read_text())

    plugins = data["details"][0]["plugins"]

    assert len(plugins) == 2

    # OK plugin → status must be "completed"
    assert plugins[0]["summary"]["status"] == "completed"

    # FAIL plugin → summary.status = "failed"
    assert plugins[1]["summary"]["status"] == "failed"


# ------------------------------------------------------------
#  B) Global status is always "completed" (engine does not compute partial/failed)
# ------------------------------------------------------------
def test_status_partial(tmp_path):
    project = tmp_path / "projB"
    project.mkdir()

    write(project / "a.py", "x = 1\n")

    plugin_ok = tmp_path / "ok.py"
    write(plugin_ok, "def run(f, c): return [{'code':'OK','severity':'low'}]\n")

    plugin_fail = tmp_path / "fail.py"
    write(plugin_fail, "def run(f, c): raise Exception('err')\n")

    write(
        project / "toolkit.toml",
        f"[plugins.OK]\npath='{plugin_ok}'\nenabled=true\n"
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n"
    )

    report = project / "report.json"

    subprocess.run(
        [sys.executable, "-m", "toolkit.core.cli", "analyze",
         str(project), "--out", str(report)],
        cwd=ROOT, text=True, capture_output=True
    )

    data = json.loads(report.read_text())

    # Engine always returns completed
    assert data["analysis_metadata"]["status"] == "completed"


# ------------------------------------------------------------
#  C) Global status completed when all succeed (unchanged)
# ------------------------------------------------------------
def test_status_completed(tmp_path):
    project = tmp_path / "projC"
    project.mkdir()

    write(project / "file.py", "x = 1\n")

    plugin_ok = tmp_path / "ok.py"
    write(plugin_ok, "def run(f, c): return [{'code':'OK'}]\n")

    write(
        project / "toolkit.toml",
        f"[plugins.OK]\npath='{plugin_ok}'\nenabled=true\n"
    )

    report = project / "report.json"

    subprocess.run(
        [sys.executable, "-m", "toolkit.core.cli", "analyze",
         str(project), "--out", str(report)],
        cwd=ROOT, capture_output=True, text=True
    )

    data = json.loads(report.read_text())

    assert data["analysis_metadata"]["status"] == "completed"


# ------------------------------------------------------------
#  D) Global status is always "completed" even if all fail
# ------------------------------------------------------------
def test_status_failed(tmp_path):
    project = tmp_path / "projD"
    project.mkdir()

    write(project / "file.py", "x = 1\n")

    plugin_fail = tmp_path / "fail.py"
    write(plugin_fail, "def run(f, c): raise Exception('boom')\n")

    write(
        project / "toolkit.toml",
        f"[plugins.FAIL]\npath='{plugin_fail}'\nenabled=true\n"
    )

    report = project / "report.json"

    subprocess.run(
        [sys.executable, "-m", "toolkit.core.cli", "analyze",
         str(project), "--out", str(report)],
        cwd=ROOT, capture_output=True, text=True
    )

    data = json.loads(report.read_text())

    # Engine always reports completed
    assert data["analysis_metadata"]["status"] == "completed"
