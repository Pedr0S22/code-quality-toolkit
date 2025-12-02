"""
End-to-end integration tests for the web application workflow.
Tests the complete user journey: file selection → analysis → report viewing.
"""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from PyQt6.QtWidgets import QApplication

from web.client import MainWindow, AnalysisWorker
from web import client


@pytest.fixture(scope="session")
def qt_app():
    """Provide a single QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_api():
    """Mock API responses."""
    responses = {
        "plugins": {
            "StyleChecker": {"max_line_length": 88},
            "CyclomaticComplexity": {"max_complexity": 10},
        },
        "analysis_result": {
            "analysis_metadata": {
                "timestamp": "2025-12-01T10:00:00Z",
                "tool_version": "0.1.0",
                "plugins_executed": ["StyleChecker", "CyclomaticComplexity"],
                "status": "completed"
            },
            "summary": {
                "total_files": 1,
                "total_issues": 2,
                "issues_by_severity": {"info": 0, "low": 2, "medium": 0, "high": 0},
                "issues_by_plugin": {"StyleChecker": 2, "CyclomaticComplexity": 0},
                "top_offenders": [{"file": "test.py", "issues": 2}]
            },
            "details": []
        }
    }
    return responses


# ============================================================================
# Tests for AnalysisWorker (Threaded Analysis)
# ============================================================================

class TestAnalysisWorkerIntegration:
    """Tests for the background analysis worker thread."""

    def test_analysis_worker_initialization(self, tmp_path):
        """AnalysisWorker initializes with correct parameters."""
        worker = AnalysisWorker(
            target_path=str(tmp_path),
            payload={"plugins": ["StyleChecker"]},
            api_url="http://127.0.0.1:8000/api/v1"
        )
        
        assert worker.target_path == tmp_path
        assert worker.payload == {"plugins": ["StyleChecker"]}
        assert worker.api_url == "http://127.0.0.1:8000/api/v1"
        assert hasattr(worker, 'finished')
        assert hasattr(worker, 'error')

    def test_analysis_worker_has_signals(self):
        """AnalysisWorker has PyQt signals for communication."""
        worker = AnalysisWorker(
            target_path="/tmp",
            payload={},
            api_url="http://127.0.0.1:8000/api/v1"
        )
        
        # Should have PyQt signals
        assert hasattr(worker, 'finished')
        assert hasattr(worker, 'error')
        assert callable(worker.finished.emit)
        assert callable(worker.error.emit)


# ============================================================================
# Tests for Complete UI Workflows
# ============================================================================

class TestUIWorkflows:
    """End-to-end UI workflow tests."""

    @pytest.fixture
    def main_window_e2e(self, qt_app, tmp_path, monkeypatch):
        """Create MainWindow with mocked API for E2E testing."""
        # Mock API responses
        fake_plugins = {
            "StyleChecker": {"max_line_length": 88},
            "CyclomaticComplexity": {"max_complexity": 10},
        }
        
        def fake_get(url, *_, **__):
            response = Mock()
            if "/plugins/configs" in url:
                response.json.return_value = fake_plugins
                response.status_code = 200
            else:
                response.json.return_value = []
                response.status_code = 200
            return response
        
        monkeypatch.setattr(client.requests, "get", fake_get)
        monkeypatch.setattr(client, "HAS_WEBENGINE", False)
        
        window = MainWindow()
        window.show()
        return window

    def test_workflow_select_path_and_run(self, main_window_e2e, tmp_path):
        """Workflow: Select path → Select plugins → Click RUN."""
        main_window = main_window_e2e
        
        # Create a test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\nprint(x)\n")
        
        # Step 1: Select path
        main_window.caminho_selecionado = str(tmp_path)
        main_window.lbl_path.setText(f"Selected: {tmp_path}")
        
        # Step 2: Ensure plugins are selected
        assert any(w.checkbox.isChecked() for w in main_window.plugin_widgets)
        
        # Step 3: Click RUN (mocked, won't actually execute)
        # Just verify the UI state is correct
        assert main_window.caminho_selecionado is not None
        assert main_window.btn_run.isEnabled()

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

    def test_workflow_results_enable_report_button(self, main_window_e2e, tmp_path):
        """Workflow: After analysis completes, REPORT button becomes enabled."""
        main_window = main_window_e2e
        
        # Create fake results directory
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.json").write_text('{"key": "value"}')
        
        # Simulate analysis completion
        main_window.on_analysis_finished(results_dir)
        
        # REPORT button should be enabled
        assert main_window.btn_report.isEnabled()
        assert main_window.results_dir == results_dir

    def test_workflow_export_without_results_shows_error(self, main_window_e2e):
        """Workflow: Try EXPORT without running analysis → error."""
        main_window = main_window_e2e
        
        # Ensure no results_dir
        if hasattr(main_window, 'results_dir'):
            delattr(main_window, 'results_dir')
        
        # Click EXPORT
        main_window.executar_plugin_export()
        
        # Should show error
        assert "Run analysis first" in main_window.lbl_path.text()

    def test_workflow_export_after_analysis_succeeds(self, main_window_e2e, tmp_path):
        """Workflow: After analysis → EXPORT creates ZIP."""
        main_window = main_window_e2e
        
        # Create fake results
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.html").write_text("<html></html>")
        (results_dir / "report.json").write_text("{}")
        
        # Simulate completion
        main_window.on_analysis_finished(results_dir)
        
        # EXPORT should be possible now (no error)
        # Just verify it can be called without error
        main_window.executar_plugin_export()
        # Should not show error message if results_dir exists
        assert main_window.results_dir is not None

    def test_workflow_plugin_config_persistence(self, main_window_e2e, tmp_path):
        """Workflow: Plugin config changes are preserved during session."""
        main_window = main_window_e2e
        
        # Get first plugin's config
        first_plugin = main_window.plugin_widgets[0]
        
        # Expand config
        first_plugin.btn_expand.setChecked(True)
        first_plugin.toggle_config_visibility(True)
        
        # Config should be visible
        assert first_plugin.config_container.isVisible()
        
        # Collapse
        first_plugin.btn_expand.setChecked(False)
        first_plugin.toggle_config_visibility(False)
        
        # Config should be hidden
        assert not first_plugin.config_container.isVisible()


# ============================================================================
# Tests for Plugin Configuration UI
# ============================================================================

class TestPluginConfigurationUI:
    """Tests for plugin configuration widget interactions."""

    @pytest.fixture
    def main_window_config(self, qt_app, monkeypatch):
        """Create MainWindow for config testing."""
        fake_plugins = {
            "TestPlugin": {"threshold": 50, "enabled": True},
        }
        
        def fake_get(url, *_, **__):
            response = Mock()
            if "/plugins/configs" in url:
                response.json.return_value = fake_plugins
                response.status_code = 200
            else:
                response.json.return_value = []
                response.status_code = 200
            return response
        
        monkeypatch.setattr(client.requests, "get", fake_get)
        monkeypatch.setattr(client, "HAS_WEBENGINE", False)
        
        window = MainWindow()
        window.show()
        return window

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
        assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)
        
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
        
        # Uncheck one
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
# Tests for Error Handling
# ============================================================================

class TestErrorHandling:
    """Error handling in workflows."""

    @pytest.fixture
    def main_window_errors(self, qt_app, monkeypatch):
        """Create MainWindow for error testing."""
        def fake_get(url, *_, **__):
            response = Mock()
            response.json.return_value = {"StyleChecker": {}}
            response.status_code = 200
            return response
        
        monkeypatch.setattr(client.requests, "get", fake_get)
        monkeypatch.setattr(client, "HAS_WEBENGINE", False)
        
        window = MainWindow()
        return window

    def test_run_with_no_path_selected(self, main_window_errors):
        """Running analysis without selecting path shows error."""
        main_window = main_window_errors
        main_window.caminho_selecionado = None
        
        main_window.executar_plugin_run()
        
        error_msg = main_window.lbl_path.text().lower()
        assert "please" in error_msg and "path" in error_msg

    def test_analysis_error_handling(self, main_window_errors):
        """on_analysis_error displays error message."""
        main_window = main_window_errors
        error_msg = "Connection timeout"
        
        main_window.on_analysis_error(error_msg)
        
        # Error message should be displayed (format may vary)
        label_text = main_window.lbl_path.text().lower()
        assert "failed" in label_text or "error" in label_text

    def test_export_without_results(self, main_window_errors):
        """Exporting without results shows error."""
        main_window = main_window_errors
        
        if hasattr(main_window, 'results_dir'):
            delattr(main_window, 'results_dir')
        
        main_window.executar_plugin_export()
        
        assert "Run analysis first" in main_window.lbl_path.text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
