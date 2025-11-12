import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_generates_report(tmp_path: Path) -> None:
    source = tmp_path / "demo.py"
    source.write_text(
        "print('hello world with a very very long line to trigger style check" \
        "warnings and exceed the default limit easily')\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "toolkit.core.cli",
            "analyze",
            str(tmp_path),
            "--out",
            str(report_path),
            "--plugins",
            "StyleChecker,CyclomaticComplexity",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        check=False,
    )

    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["total_files"] == 1
    assert report["summary"]["total_issues"] >= 1
