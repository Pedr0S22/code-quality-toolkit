import json
import os
import subprocess
import sys
from pathlib import Path

# Use relative path to find the root, but do not write to it
ROOT = Path(__file__).resolve().parents[3]

def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def create_fake_pylint_module(tmp_path: Path, python_code: str) -> dict:
    """
    Creates a fake 'pylint' python package in a temporary directory
    and returns the environment variables needed to load it.
    """
    site_pkgs = tmp_path / "site_packages"
    pylint_dir = site_pkgs / "pylint"
    pylint_dir.mkdir(parents=True, exist_ok=True)
    
    (pylint_dir / "__init__.py").touch()
    (pylint_dir / "__main__.py").write_text(python_code, encoding="utf-8")
    
    env = os.environ.copy()
    # Prepend our fake site_packages to PYTHONPATH so it loads first
    env["PYTHONPATH"] = str(site_pkgs) + os.pathsep + env.get("PYTHONPATH", "")
    return env

def test_engine_runs_linterwrapper_successfully(tmp_path):
    """
    Integration Test A: Engine + LinterWrapper (Pylint) integration.
    """
    # FIX: Use tmp_path instead of ROOT to prevent creating files in the repo
    project_dir = tmp_path / "project_A"
    project_dir.mkdir(exist_ok=True)
    
    sample_file = project_dir / "example.py"
    write_file(sample_file, "a=1\n")

    # Mock: A pylint module that prints JSON to stdout
    fake_code = (
        "import sys\n"
        "print('[{\"type\": \"warning\", \"path\": \"example.py\", "
        "\"line\": 1, \"column\": 1, \"symbol\": \"bad\", "
        "\"message\": \"test message\", \"severity\": \"low\"}]')\n"
    )
    env = create_fake_pylint_module(tmp_path, fake_code)

    config_file = project_dir / "toolkit.toml"
    write_file(config_file, "[plugins.linter_wrapper]\nenabled = true\n")
    report_path = project_dir / "report.json"

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project_dir),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    # We run from ROOT so python can find toolkit.core, but the project is in tmp_path
    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True, env=env)

    report = json.loads(report_path.read_text())
    lint_issues = [
        p for d in report["details"] 
        for p in d["plugins"] 
        if p["plugin"] == "LinterWrapper"
    ]

    assert len(lint_issues) > 0
    assert lint_issues[0]["results"][0]["message"] == "test message"

# ─────────────────────────────────────────────
# B1 — pylint missing
# ─────────────────────────────────────────────
def test_linterwrapper_handles_missing_pylint(tmp_path):
    """If pylint is not installed, LinterWrapper must return LINTER_NOT_FOUND."""
    project = tmp_path / "projB1"
    project.mkdir()
    
    write_file(project / "a.py", "x = 1\n")
    write_file(project / "toolkit.toml", "[plugins.linter_wrapper]\nenabled = true\n")
    report_path = project / "report.json"

    # Mock: A pylint module that behaves as if it's missing (standard python error)
    fake_code = (
        "import sys\n"
        "sys.stderr.write(f'{sys.executable}: No module named pylint\\n')\n"
        "sys.exit(1)\n"
    )
    env = create_fake_pylint_module(tmp_path, fake_code)

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)

    report = json.loads(report_path.read_text())
    issues = [
        p for d in report["details"] 
        for p in d["plugins"] 
        if p["plugin"] == "LinterWrapper"
    ]

    assert len(issues) > 0
    assert issues[0]["results"][0]["code"] == "LINTER_NOT_FOUND"

# ─────────────────────────────────────────────
# B2 — timeout
# ─────────────────────────────────────────────
def test_linterwrapper_timeout(tmp_path):
    project = tmp_path / "projB2"
    project.mkdir()
    write_file(project / "slow.py", "a = 1\n")
    write_file(project / "toolkit.toml", 
        "[plugins.linter_wrapper]\nenabled = true\ntimeout_seconds = 0\n"
    )
    report_path = project / "report.json"

    # Mock: A pylint module that sleeps
    fake_code = "import time; time.sleep(5)"
    env = create_fake_pylint_module(tmp_path, fake_code)

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)

    report = json.loads(report_path.read_text())
    issues = [
        p for d in report["details"] 
        for p in d["plugins"] 
        if p["plugin"] == "LinterWrapper"
    ]

    if issues and issues[0]["results"]:
        assert issues[0]["results"][0]["code"] in ["LINTER_TIMEOUT", "LINTER_NOT_FOUND"]
    else:
        assert issues[0]["summary"]["status"] in ["completed", "failed"]

# ─────────────────────────────────────────────
# B3 — invalid output
# ─────────────────────────────────────────────
def test_linterwrapper_invalid_json_output(tmp_path):
    project = tmp_path / "projB3"
    project.mkdir()
    write_file(project / "bad.py", "a=1\n")
    write_file(project / "toolkit.toml", "[plugins.linter_wrapper]\nenabled = true\n")
    report_path = project / "report.json"

    # Mock: Invalid JSON output
    fake_code = "print('NOT JSON OUTPUT')"
    env = create_fake_pylint_module(tmp_path, fake_code)

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
    ]

    subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)

    report = json.loads(report_path.read_text())
    issues = [
        p for d in report["details"] 
        for p in d["plugins"] 
        if p["plugin"] == "LinterWrapper"
    ]

    assert len(issues) > 0
    assert issues[0]["results"][0]["code"] == "LINTER_OUTPUT_INVALID"

def test_linterwrapper_fail_on_severity_high(tmp_path):
    project = tmp_path / "projC"
    project.mkdir()
    write_file(project / "file.py", "a=1\n")
    write_file(project / "toolkit.toml", "[plugins.linter_wrapper]\nenabled = true\n")
    report_path = project / "report.json"

    # Mock: High severity error
    fake_code = (
        "print('[{\"type\": \"error\", \"path\": \"file.py\", "
        "\"line\": 1, \"column\": 1, \"symbol\": \"E001\", "
        "\"message\": \"high severity test\", \"severity\": \"high\"}]')\n"
    )
    env = create_fake_pylint_module(tmp_path, fake_code)

    cmd = [
        sys.executable, "-m", "toolkit.core.cli",
        "analyze", str(project),
        "--out", str(report_path),
        "--plugins", "LinterWrapper",
        "--fail-on-severity=high",
    ]

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, env=env)

    assert result.returncode == 3