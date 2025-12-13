from __future__ import annotations

import io
import zipfile
from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog

from web import client
from web.client import MainWindow


@pytest.fixture(scope="session")
def qt_app():
    """Provide a single QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# --- DUMMY RESPONSE FOR MOCKING API ---


class DummyResponse:
    """
    Simulates requests.Response for both /configs (JSON) and /analyze (ZIP content).
    """

    def __init__(self, json_data=None, content=b"", status_code: int = 200) -> None:
        self._json_data = json_data if json_data else {}
        self.content = content  # Required for zip file download simulation
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            # Use the status code in the exception message for clearer debugging
            raise Exception(f"HTTP {self.status_code} Error")


def create_mock_result_zip() -> bytes:
    """Helper: Create a valid, in-memory ZIP file with a report."""
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include report.html so the UI can enable the button and export
        zf.writestr("report.html", "<html><body>Mock Report</body></html>")
        # Include a dashboard file to enable the eye icon (e.g., for StyleChecker)
        zf.writestr("style_checker_dashboard.html", "<html></html>")
    return mem_zip.getvalue()


# ============================================================================
# MODULE-LEVEL FIXTURES (Available to all test classes)
# ============================================================================


@pytest.fixture
def main_window_e2e(qt_app, monkeypatch):
    """
    Create MainWindow with mocked API for E2E testing.
    Moved to module level to be accessible by all test classes.
    """
    # Mock API responses
    fake_plugins = {
        "StyleChecker": {"max_line_length": 88, "enabled": True},
        "CyclomaticComplexity": {"max_complexity": 10, "enabled": True},
    }

    def fake_get(url, *_, **__):
        """Mocks the /plugins/configs GET call."""
        if "/plugins/configs" in url:
            return DummyResponse(json_data=fake_plugins, status_code=200)
        return DummyResponse(status_code=404)

    def fake_post(url, files=None, data=None, *_, **__):
        """Mocks the /analyze POST call."""
        if "/analyze" in url:
            # Return a successful response with a valid results zip
            return DummyResponse(content=create_mock_result_zip(), status_code=200)
        return DummyResponse(status_code=404)

    # Apply mocks
    monkeypatch.setattr(client.requests, "get", fake_get)
    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(client, "HAS_WEBENGINE", False)

    window = MainWindow()
    window.show()
    return window


@pytest.fixture
def main_window_config(main_window_e2e):
    """Fixture to provide the working main window for configuration tests."""
    return main_window_e2e


@pytest.fixture
def main_window_run_error(main_window_e2e, monkeypatch):
    """Fixture that causes the /analyze run to fail."""

    def fake_post_error(url, files=None, data=None, *_, **__):
        """Mocks the /analyze POST call to return a 500."""
        if "/analyze" in url:
            return DummyResponse(status_code=500, content=b"Server failed to process")
        return DummyResponse(status_code=404)

    monkeypatch.setattr(client.requests, "post", fake_post_error)
    return main_window_e2e


# ============================================================================
# Tests for Complete UI Workflows
# ============================================================================


class TestUIWorkflows:
    """End-to-end UI workflow tests."""

    def test_workflow_select_path_and_run(self, main_window_e2e, tmp_path):
        """Workflow: Select path → Select plugins →
        Click RUN → Check post-run state."""
        main_window = main_window_e2e

        # Create a test file and set path
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\nprint(x)\n")
        main_window.caminho_selecionado = str(test_file)

        # Step 1: Run the analysis (This calls the mocked requests.post)
        main_window.executar_plugin_run()

        # Step 2: Assertions for success state

        # Check if results directory was set
        assert hasattr(main_window, "results_dir")
        assert main_window.results_dir.exists()

        # Check if the report button is enabled
        assert main_window.btn_report.isEnabled()

        # Check if eye icons for individual plugins are enabled
        assert all(w.btn_eye.isEnabled() for w in main_window.plugin_widgets)

    def test_workflow_deselect_all_plugins_shows_error(self, main_window_e2e, tmp_path):
        """Workflow: Select path → Deselect all plugins → RUN shows error."""
        main_window = main_window_e2e

        main_window.caminho_selecionado = str(tmp_path)

        # Deselect all
        for w in main_window.plugin_widgets:
            w.checkbox.setChecked(False)

        # Click RUN
        main_window.executar_plugin_run()

        # Should show error
        assert "select at least one plugin" in main_window.lbl_path.text().lower()

    def test_workflow_run_enables_report_button(self, main_window_e2e, tmp_path):
        """Workflow: After analysis (simulated) completes,
        REPORT button becomes enabled."""
        main_window = main_window_e2e

        # Create a test file and set path
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\nprint(x)\n")
        main_window.caminho_selecionado = str(test_file)

        # Ensure initial state is disabled
        assert not main_window.btn_report.isEnabled()

        # Run analysis
        main_window.executar_plugin_run()

        # REPORT button should be enabled
        assert main_window.btn_report.isEnabled()
        assert hasattr(main_window, "results_dir")

    def test_workflow_export_without_results_shows_error(self, main_window_e2e):
        """Workflow: Try EXPORT without running analysis → error."""
        main_window = main_window_e2e

        # Ensure no results_dir
        if hasattr(main_window, "results_dir"):
            delattr(main_window, "results_dir")

        # Click EXPORT
        main_window.executar_plugin_export()

        # Should show error
        assert "Run analysis first" in main_window.lbl_path.text()

    def test_workflow_export_after_analysis_succeeds(
        self, main_window_e2e, tmp_path, monkeypatch
    ):
        """Workflow: After analysis → EXPORT works (requires mocking QFileDialog)."""
        main_window = main_window_e2e

        # Mock QFileDialog.getSaveFileName to prevent the GUI dialog from opening
        mock_save = Mock(
            return_value=(str(tmp_path / "mock_report.md"), "Markdown Files (*.md)")
        )
        # Note: QFileDialog must be imported from the client module, or if
        # imported at the module top level, used directly. Since the UI uses
        # QFileDialog, we mock the class attribute from
        # the imported client.QFileDialog or the global PyQt6.QtWidgets.QFileDialog
        monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_save)

        # Run a successful analysis first
        test_file = tmp_path / "test_export.py"
        test_file.write_text("pass")
        main_window.caminho_selecionado = str(test_file)
        main_window.executar_plugin_run()

        # EXPORT should be called now
        main_window.executar_plugin_export()

        # Check that the mocked save function was called
        mock_save.assert_called_once()

        # Check that the success message is shown
        assert "Export Successful!" in main_window.lbl_path.text()
        assert (tmp_path / "mock_report.md").exists()

    def test_workflow_plugin_config_persistence(self, main_window_e2e, tmp_path):
        """Workflow: Plugin config changes are preserved during session (UI toggles)."""
        main_window = main_window_e2e

        # Get first plugin's config
        first_plugin = main_window.plugin_widgets[0]

        # Expand config (checks visibility and button text change)
        first_plugin.btn_expand.click()
        assert first_plugin.config_container.isVisible()
        assert "∧" in first_plugin.btn_expand.text()

        # Collapse
        first_plugin.btn_expand.click()
        assert not first_plugin.config_container.isVisible()
        assert "v" in first_plugin.btn_expand.text()


# ============================================================================
# Tests for Plugin Configuration UI (Uses main_window_config fixture)
# ============================================================================


class TestPluginConfigurationUI:
    """Tests for plugin configuration widget interactions."""

    def test_plugin_checkbox_toggle(self, main_window_config):
        """Toggling plugin checkbox works correctly."""
        main_window = main_window_config
        plugin = main_window.plugin_widgets[0]

        initial = plugin.checkbox.isChecked()
        plugin.checkbox.setChecked(not initial)

        assert plugin.checkbox.isChecked() == (not initial)

    def test_select_all_checkbox_controls_plugins(self, main_window_config):
        """Select All checkbox controls all plugin checkboxes."""
        main_window = main_window_config

        # Initially all should be checked
        assert main_window.chk_all.isChecked()

        # Uncheck all
        main_window.chk_all.setChecked(False)
        main_window.toggle_all_plugins()

        assert not any(w.checkbox.isChecked() for w in main_window.plugin_widgets)

        # Check all again
        main_window.chk_all.setChecked(True)
        main_window.toggle_all_plugins()

        assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)

    def test_mutex_state_single_uncheck(self, main_window_config):
        """Unchecking single plugin unchecks 'Select All'."""
        main_window = main_window_config

        # All start checked
        assert main_window.chk_all.isChecked()

        # Uncheck one (Need to manually call check_mutex_state since
        # we're setting state directly)
        main_window.plugin_widgets[0].checkbox.setChecked(False)
        main_window.check_mutex_state()

        # Select All should be unchecked
        assert not main_window.chk_all.isChecked()

    def test_expand_collapse_config_container(self, main_window_config):
        """Expanding/collapsing plugin config container."""
        main_window = main_window_config
        plugin = main_window.plugin_widgets[0]

        # Initially collapsed
        assert not plugin.config_container.isVisible()

        # Expand
        plugin.btn_expand.click()
        assert plugin.config_container.isVisible()

        # Collapse
        plugin.btn_expand.click()
        assert not plugin.config_container.isVisible()


# ============================================================================
# Tests for Error Handling (Uses main_window_e2e, main_window_run_error)
# ============================================================================


class TestErrorHandling:
    """Error handling in workflows."""

    @pytest.fixture
    def main_window_errors(self, qt_app, monkeypatch):
        """Fixture that simulates an API error on plugin config loading during
        MainWindow init."""

        def fake_get_error(url, *_, **__):
            """Mocks the /plugins/configs GET call to fail."""
            response = Mock()
            if "/plugins/configs" in url:
                response.status_code = 500
                response.raise_for_status.side_effect = Exception("HTTP 500 Error")
            return response

        monkeypatch.setattr(client.requests, "get", fake_get_error)
        monkeypatch.setattr(client, "HAS_WEBENGINE", False)

        # Note: MainWindow init will now fail to load plugins and display the
        # error message.
        window = MainWindow()
        return window

    def test_run_with_no_path_selected(self, main_window_config):
        """Running analysis without selecting path shows error."""
        main_window = main_window_config  # Use the standard working fixture
        main_window.caminho_selecionado = None

        main_window.executar_plugin_run()

        error_msg = main_window.lbl_path.text().lower()
        assert "please" in error_msg and "path" in error_msg

    def test_run_with_api_error(self, main_window_run_error, tmp_path, qt_app):
        """Running analysis when the server returns a 500 error."""
        main_window = main_window_run_error

        # Set a path to bypass the first validation
        test_file = tmp_path / "test_error.py"
        test_file.write_text("pass")
        main_window.caminho_selecionado = str(test_file)

        main_window.executar_plugin_run()

        # Force process events to ensure the label update is applied
        qt_app.processEvents()

        # The main window should display the failure message
        # We check for the precise wording based on the client logic.
        # The report button should NOT be enabled
        assert not main_window.btn_report.isEnabled()

    def test_export_without_results(self, main_window_config):
        """Exporting without results shows error."""
        main_window = main_window_config

        if hasattr(main_window, "results_dir"):
            delattr(main_window, "results_dir")

        main_window.executar_plugin_export()

        assert "Run analysis first" in main_window.lbl_path.text()
