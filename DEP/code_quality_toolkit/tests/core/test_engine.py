from pathlib import Path

from toolkit.core.engine import run_analysis
from toolkit.utils.config import ToolkitConfig


class WorkingPlugin:
    def get_metadata(self) -> dict:
        return {"name": "Working", "version": "1.0", "description": "ok"}

    def analyze(self, source_code: str, file_path: str | None) -> dict:
        return {
            "results": [],
            "summary": {"issues_found": 0, "status": "completed"},
        }


class FailingPlugin:
    def get_metadata(self) -> dict:
        return {"name": "Failing", "version": "1.0", "description": "boom"}

    def analyze(self, source_code: str, file_path: str | None) -> dict:
        raise RuntimeError("boom")


def test_engine_marks_partial_when_plugin_fails(tmp_path: Path) -> None:
    source = tmp_path / "code.py"
    source.write_text("print('hi')\n", encoding="utf-8")

    config = ToolkitConfig()
    plugins = {"Working": WorkingPlugin(), "Failing": FailingPlugin()}

    files, status = run_analysis(tmp_path, plugins, config)

    assert status["Failing"] == "partial"
    assert files[0]["plugins"][1]["summary"]["status"] == "failed"
