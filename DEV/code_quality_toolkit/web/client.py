import os
import sys
import tempfile
import zipfile
from pathlib import Path

import json
from typing import Any, Dict

from typing import Dict, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtCore import QThread


import json
import requests

API_BASE_URL = "http://127.0.0.1:8000"
ANALYZE_URL = f"{API_BASE_URL}/api/v1/analyze"


def compress_target(target: str) -> Path:
    """Create a zip from a file or directory.

    If Path is Directory: zip the folder contents recursively.
    If Path is File:      create a zip and add the single file at the root.

    Returns:
        Path to the created zip file inside a temporary directory.

    Raises:
        ValueError: if the target path does not exist.
    """
    target_path = Path(target).expanduser().resolve()
    if not target_path.exists():
        raise ValueError(f"Target path does not exist: {target_path}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="toolkit_client_"))
    zip_path = tmp_dir / "target.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if target_path.is_dir():
            for root, _, files in os.walk(target_path):
                root_path = Path(root)
                for name in files:
                    file_path = root_path / name
                    arcname = file_path.relative_to(target_path)
                    zf.write(file_path, arcname=str(arcname))
        else:
            # single file at root
            zf.write(target_path, arcname=target_path.name)

    return zip_path



def load_report(path: str = "report.json") -> Dict[str, Any]:
    """Load the JSON report from disk and return it as a Python dict."""
    report_path = Path(path)
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    text = report_path.read_text(encoding="utf-8")
    return json.loads(text)


class PluginSelectionController(QObject):
    """Keeps track of plugin selection and 'Select All' behaviour.

    The UI layer can:
      - call set_select_all(True/False) when the master checkbox changes
      - call set_plugin_checked(name, bool) when an individual checkbox changes
      - listen to selection_changed & select_all_changed signals
    """

    selection_changed = pyqtSignal(list)  # list[str] of selected plugin names
    select_all_changed = pyqtSignal(bool)

    def __init__(self, plugin_names: List[str]) -> None:
        super().__init__()
        self._plugins: Dict[str, bool] = {name: True for name in plugin_names}
        self._select_all = True

    @property
    def selected_plugins(self) -> List[str]:
        return [name for name, checked in self._plugins.items() if checked]

    @property
    def select_all(self) -> bool:
        return self._select_all

    def set_select_all(self, checked: bool) -> None:
        """Called when the 'Select All' checkbox is toggled."""
        self._select_all = checked
        for name in self._plugins:
            self._plugins[name] = checked
        self.select_all_changed.emit(checked)
        self.selection_changed.emit(self.selected_plugins)

    def set_plugin_checked(self, name: str, checked: bool) -> None:
        """Called when an individual plugin checkbox is toggled."""
        if name not in self._plugins:
            return
        self._plugins[name] = checked

        # update master state: only true if all are checked
        all_checked = all(self._plugins.values())
        if all_checked != self._select_all:
            self._select_all = all_checked
            self.select_all_changed.emit(self._select_all)

        self.selection_changed.emit(self.selected_plugins)


class AnalysisWorker(QObject):
    """Runs compress → POST /analyze → save report.json in background."""

    finished = pyqtSignal(str)  # path to report.json
    error = pyqtSignal(str)     # human-readable error message

    def __init__(self, target_path: str, selected_plugins: List[str]) -> None:
        super().__init__()
        self._target_path = target_path
        self._selected_plugins = selected_plugins

    def run(self) -> None:
        try:
            # 1) Compress (this can raise ValueError for bad paths)
            zip_path = compress_target(self._target_path)

            # 2) Build plugins field
            plugins_value = ",".join(self._selected_plugins) if self._selected_plugins else "all"

            # 3) POST /api/v1/analyze
            with open(zip_path, "rb") as f:
                files = {"file": ("target.zip", f, "application/zip")}
                data = {"plugins": plugins_value}
                try:
                    resp = requests.post(ANALYZE_URL, files=files, data=data, timeout=120)
                except requests.RequestException as exc:
                    # Server offline / network error
                    raise RuntimeError(f"Server unavailable or network error: {exc}") from exc

            if resp.status_code != 200:
                # e.g. invalid zip, invalid plugins, internal error, etc.
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"Server returned {resp.status_code}: {detail}")

            # 4) Save report.json
            report_path = Path.cwd() / "report.json"
            report_path.write_bytes(resp.content)

            # verify JSON
            json.loads(report_path.read_text(encoding="utf-8"))

            self.finished.emit(str(report_path))

        except Exception as exc:  # propagate any error via signal (no crash)
            self.error.emit(str(exc))


class AnalysisController(QObject):
    """High-level helper to run AnalysisWorker in a QThread.

    The UI layer only needs to:
      - connect to analysis_started / analysis_finished / analysis_error
      - call run_analysis(path, selected_plugins)
    """

    analysis_started = pyqtSignal()
    analysis_finished = pyqtSignal(str)  # path to report.json
    analysis_error = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None

    def run_analysis(self, target_path: str, selected_plugins: List[str]) -> None:
        """Start background analysis with basic pre-validation."""
        p = Path(target_path).expanduser()
        if not p.exists():
            self.analysis_error.emit(f"Target path does not exist: {p}")
            return

        self._thread = QThread(self)
        self._worker = AnalysisWorker(str(p), selected_plugins)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)

        self.analysis_started.emit()
        self._thread.start()

    def _on_worker_finished(self, report_path: str) -> None:
        self.analysis_finished.emit(report_path)

    def _on_worker_error(self, message: str) -> None:
        self.analysis_error.emit(message)

