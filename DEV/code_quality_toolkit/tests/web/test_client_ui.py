from __future__ import annotations

import io
import zipfile

import pytest

# --- CI PROTECTION BLOCK ---
pytest.importorskip("PyQt6")

try:
    from PyQt6.QtWidgets import QApplication

    # Importing 'client' assuming the UI code provided is saved as web/client.py
    from web import client
    from web.client import MainWindow
except ImportError:
    pytest.skip("UI libraries or application code not installed")
# -----------------------------


@pytest.fixture(scope="session")
def app():
    """Ensures a single QApplication instance for all tests."""
    qt_app = QApplication.instance()
    if qt_app is None:
        qt_app = QApplication([])
    return qt_app


class DummyResponse:
    """
    Fake response to simulate GET (configs) and POST (analysis zip).
    Now includes .content for file downloads.
    """

    def __init__(self, json_data=None, content=b"", status_code: int = 200) -> None:
        self._json_data = json_data if json_data else {}
        self.content = content  # Required for zip file download simulation
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def main_window(app, monkeypatch):
    """
    Creates the MainWindow in a controlled state with mocked API.
    """
    # 1) Disable WebEngine (simulating environment without it or to speed up tests)
    monkeypatch.setattr(client, "HAS_WEBENGINE", False, raising=False)

    # 2) Fake API /plugins/configs (GET)
    fake_plugins = {
        "StyleChecker": {"max_line_length": 88},
        "CyclomaticComplexity": {"max_complexity": 10},
    }

    def fake_get(url, *_, **__):
        if url.endswith("/plugins/configs"):
            return DummyResponse(json_data=fake_plugins)
        return DummyResponse(status_code=404)

    # 3) Fake API /analyze (POST) - Returns a valid ZIP file in bytes
    def fake_post(url, files=None, data=None, *_, **__):
        if url.endswith("/analyze"):
            # Create a valid in-memory zip file to return
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add a dummy report.html so the UI finds it
                zf.writestr("report.html", "<html><body>Mock Report</body></html>")
                # Add a dummy dashboard
                zf.writestr("style_checker_dashboard.html", "<html></html>")

            return DummyResponse(content=mem_zip.getvalue(), status_code=200)
        return DummyResponse(status_code=404)

    # Apply mocks to the 'requests' module imported inside 'client'
    monkeypatch.setattr(client.requests, "get", fake_get)
    monkeypatch.setattr(client.requests, "post", fake_post)

    # 4) Create Main Window
    # The constructor calls load_plugins(), which triggers our fake_get
    win = MainWindow()
    return win


# ---------- UI / LOGIC TESTS ----------


def test_select_all_checks_and_unchecks_individual(main_window):
    """Test that the 'Select All' checkbox toggles all individual plugins."""
    # Verify initial state (all checked by default)
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)
    assert main_window.chk_all.isChecked()

    # Uncheck All
    main_window.chk_all.setChecked(False)
    main_window.toggle_all_plugins()
    assert not any(w.checkbox.isChecked() for w in main_window.plugin_widgets)

    # Check All
    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)


def test_unchecking_single_plugin_unchecks_select_all(main_window):
    """Test that unchecking one plugin deselects the 'Select All' checkbox."""
    # Ensure all are checked first
    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()

    # Uncheck the first plugin
    first = main_window.plugin_widgets[0]
    first.checkbox.setChecked(False)
    # Note: In the actual UI code, the widget connects stateChanged ->
    # check_mutex_state,
    # but in unit tests without a running event loop, we sometimes need to
    # call the slot manually
    # if we programmatically change the state, or rely on signals.
    # The UI code: self.checkbox.stateChanged.connect(self.on_checkbox_changed)
    # manual trigger for test safety:
    main_window.check_mutex_state()

    assert not main_window.chk_all.isChecked()


def test_run_without_path_shows_error_in_label(main_window):
    """Test validation: Run button should fail if no path is selected."""
    main_window.caminho_selecionado = None
    main_window.executar_plugin_run()

    # Check that error message is set in the label
    assert "Please, select a path" in main_window.lbl_path.text()
    # Button should remain enabled
    assert main_window.btn_run.isEnabled()


def test_run_without_any_plugin_selected_shows_error(main_window, tmp_path):
    """Test validation: Run button should fail if no plugins are selected."""
    main_window.caminho_selecionado = str(tmp_path)

    # Uncheck all widgets
    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(False)

    main_window.executar_plugin_run()

    assert "Please, select at least one plugin" in main_window.lbl_path.text()
    assert main_window.btn_run.isEnabled()


def test_run_success_enables_report_and_eyes(main_window, tmp_path):
    """
    Test the full success flow of executing the run button.
    Since 'on_analysis_finished' no longer exists, we test 'executar_plugin_run'
    mocking the network response.
    """
    # 1. Setup a dummy target file to analyze
    target_file = tmp_path / "dummy_code.py"
    target_file.write_text("print('hello')")
    main_window.caminho_selecionado = str(target_file)

    # 2. Ensure plugins are checked
    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(True)

    # 3. Trigger the Run Action
    # This calls requests.post (mocked), receives the zip, extracts it, and updates UI
    main_window.executar_plugin_run()

    # 4. Assertions
    # Check if results_dir was set
    assert hasattr(main_window, "results_dir")
    assert main_window.results_dir.exists()

    # Check if report button was enabled
    assert main_window.btn_report.isEnabled()

    # Check if plugin "Eye" buttons were enabled
    for w in main_window.plugin_widgets:
        assert w.btn_eye.isEnabled()
        assert w.btn_eye.text() == "👁"


def test_export_without_running_analysis_shows_message(main_window):
    """Test that Export fails cleanly if analysis hasn't run yet."""
    # Ensure clean state
    if hasattr(main_window, "results_dir"):
        delattr(main_window, "results_dir")

    main_window.executar_plugin_export()

    # UI message when results_dir doesn't exist
    assert "Run analysis first" in main_window.lbl_path.text()
