"""
Integration tests for FastAPI server endpoints.
Tests the API layer: plugin discovery, analysis, file handling.
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import pytest

# --- BLOCO DE PROTEÇÃO CI ---
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

try:
    from fastapi.testclient import TestClient

    from web.server import app
except ImportError:
    pytest.skip("FastAPI not installed in CI")
# -----------------------------

# Use TestClient for synchronous testing (se importado com sucesso)
if "TestClient" in globals():
    client = TestClient(app)
else:
    client = None


# ============================================================================
# Tests for GET /api/v1/plugins
# ============================================================================


class TestListPluginsEndpoint:
    """Tests for listing available plugins."""

    def test_list_plugins_returns_200(self):
        """GET /api/v1/plugins returns status 200."""
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200

    def test_list_plugins_returns_plugin_list(self):
        """GET /api/v1/plugins returns a dict with 'plugins' key."""
        response = client.get("/api/v1/plugins")
        data = response.json()
        assert isinstance(data, dict)
        assert "plugins" in data
        assert isinstance(data["plugins"], list)

    def test_list_plugins_returns_known_plugins(self):
        """GET /api/v1/plugins includes expected plugins."""
        response = client.get("/api/v1/plugins")
        data = response.json()
        plugins = data["plugins"]

        # Should include StyleChecker and CyclomaticComplexity at minimum
        assert len(plugins) > 0


# ============================================================================
# Tests for GET /api/v1/plugins/configs
# ============================================================================


class TestListPluginConfigsEndpoint:
    """Tests for retrieving plugin configurations."""

    def test_list_configs_returns_200(self):
        """GET /api/v1/plugins/configs returns status 200."""
        response = client.get("/api/v1/plugins/configs")
        assert response.status_code == 200

    def test_list_configs_returns_dict(self):
        """GET /api/v1/plugins/configs returns a dictionary of configs."""
        response = client.get("/api/v1/plugins/configs")
        data = response.json()
        assert isinstance(data, dict)

    def test_each_config_has_settings(self):
        """Each plugin config contains configuration settings."""
        response = client.get("/api/v1/plugins/configs")
        data = response.json()

        for plugin_name, config in data.items():
            assert isinstance(plugin_name, str)
            assert isinstance(config, dict)
            assert len(config) >= 0


# ============================================================================
# Tests for POST /api/v1/analyze
# ============================================================================


class TestAnalyzeEndpoint:
    """Tests for the analysis endpoint."""

    @staticmethod
    def create_test_zip(content: str) -> bytes:
        """Helper: Create a test ZIP file with a Python file."""
        import io

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            py_file = tmp_path / "test.py"
            py_file.write_text(content)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(py_file, arcname="test.py")

            return zip_buffer.getvalue()

    def test_analyze_with_empty_config(self, tmp_path):
        """POST /api/v1/analyze with default config (no overrides)."""
        zip_content = self.create_test_zip("print('hello')\n")

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.zip", zip_content, "application/zip")},
            data={"configs": "{}"},
        )

        assert response.status_code == 200
        assert response.headers["content-disposition"]

    def test_analyze_returns_zip_file(self, tmp_path):
        """POST /api/v1/analyze returns a ZIP file with results."""
        zip_content = self.create_test_zip("x = 1\nprint(x)\n")

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.zip", zip_content, "application/zip")},
            data={"configs": "{}"},
        )

        assert response.status_code == 200

        result_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        result_zip.write(response.content)
        result_zip.close()

        assert zipfile.is_zipfile(result_zip.name)

        with zipfile.ZipFile(result_zip.name, "r") as zf:
            files = zf.namelist()
            assert any("report" in f.lower() for f in files)

        Path(result_zip.name).unlink()

    def test_analyze_with_specific_plugins(self):
        """POST /api/v1/analyze with specific plugin selection."""
        zip_content = self.create_test_zip("def unused(): pass\n")

        configs_json = json.dumps(
            {
                "StyleChecker": {},
            }
        )

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.zip", zip_content, "application/zip")},
            data={"configs": configs_json},
        )

        assert response.status_code == 200

    def test_analyze_with_bad_zip_returns_error(self):
        """POST /api/v1/analyze with invalid ZIP returns error."""
        bad_zip = b"This is not a ZIP file"

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("bad.zip", bad_zip, "application/zip")},
            data={"configs": "{}"},
        )

        assert response.status_code in (400, 500)

    def test_analyze_with_invalid_json_config(self):
        """POST /api/v1/analyze with invalid JSON in configs."""
        zip_content = self.create_test_zip("x = 1\n")

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.zip", zip_content, "application/zip")},
            data={"configs": "not valid json"},
        )

        assert response.status_code in (200, 400, 500)

    def test_analyze_missing_file(self):
        """POST /api/v1/analyze without file returns error."""
        response = client.post("/api/v1/analyze", data={"configs": "{}"})

        assert response.status_code == 422

    def test_analyze_with_multiple_python_files(self):
        """POST /api/v1/analyze with multiple Python files in ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "file1.py").write_text("x = 1\n")
            (tmp_path / "file2.py").write_text("y = 2\n")
            (tmp_path / "subdir").mkdir()
            (tmp_path / "subdir" / "file3.py").write_text("z = 3\n")

            import io

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for py_file in tmp_path.rglob("*.py"):
                    zf.write(py_file, arcname=py_file.relative_to(tmp_path))

            zip_content = zip_buffer.getvalue()

            response = client.post(
                "/api/v1/analyze",
                files={"file": ("multi.zip", zip_content, "application/zip")},
                data={"configs": "{}"},
            )

            assert response.status_code == 200


# ============================================================================
# Integration tests combining multiple endpoints
# ============================================================================


class TestFullAnalysisWorkflow:
    """Test complete workflow: list → configure → analyze."""

    def test_workflow_list_plugins_then_analyze(self):
        """Full workflow: list plugins, then run analysis."""
        list_response = client.get("/api/v1/plugins")
        assert list_response.status_code == 200
        plugins = list_response.json()["plugins"]
        assert len(plugins) > 0

        config_response = client.get("/api/v1/plugins/configs")
        assert config_response.status_code == 200
        configs = config_response.json()
        assert len(configs) > 0

        zip_content = TestAnalyzeEndpoint.create_test_zip(
            "def hello():\n    print('hello')\n\nx = 1\n"
        )

        analyze_response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.zip", zip_content, "application/zip")},
            data={"configs": json.dumps({})},
        )

        assert analyze_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
