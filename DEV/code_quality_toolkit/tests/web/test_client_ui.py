from __future__ import annotations
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# --- BLOCO DE PROTEÇÃO CI ---
# Tenta importar as bibliotecas de UI. Se falhar (no CI), salta os testes.
pytest.importorskip("PyQt6")

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    from web import client  # Importa o módulo 'client' para o monkeypatch funcionar
    from web.client import MainWindow, AnalysisWorker
    
except ImportError:
    pytest.skip("UI libraries not installed (Running in CI?)", allow_module_level=True)
# -----------------------------

@pytest.fixture(scope="session")
def app():
    """Garante uma única QApplication para todos os testes."""
    qt_app = QApplication.instance()
    if qt_app is None:
        qt_app = QApplication([])
    return qt_app


class DummyResponse:
    """Resposta falsa para simular GET /plugins/configs."""

    def __init__(self, payload, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


class DummySignal:
    """Sinal mínimo compatível com .connect usado no DummyWorker."""

    def connect(self, *_, **__):
        pass


class DummyWorker:
    """
    Stand-in para AnalysisWorker usado nos testes de UI.
    """

    def __init__(self, target_path, payload, api_url) -> None:
        self.target_path = Path(target_path)
        self.payload = payload
        self.api_url = api_url
        self.finished = DummySignal()
        self.error = DummySignal()

    def start(self) -> None:
        pass


@pytest.fixture
def main_window(app, monkeypatch):
    """
    Cria a MainWindow num estado controlado.
    """
    # 1) Desativa WebEngine (Agora funciona porque 'client' foi importado)
    monkeypatch.setattr(client, "HAS_WEBENGINE", False, raising=False)

    # 2) Finge API /plugins/configs
    fake_plugins = {
        "StyleChecker": {"max_line_length": 88},
        "CyclomaticComplexity": {"max_complexity": 10},
    }

    def fake_get(url, *_, **__):
        assert url.endswith("/plugins/configs")
        return DummyResponse(fake_plugins)

    monkeypatch.setattr(client.requests, "get", fake_get)

    # 3) Substitui AnalysisWorker por DummyWorker
    monkeypatch.setattr(client, "AnalysisWorker", DummyWorker)

    # 4) Cria janela principal
    win = MainWindow()
    return win


# ---------- TESTES DE UI / LÓGICA DE ESTADO ----------

def test_select_all_checks_and_unchecks_individual(main_window):
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)
    assert main_window.chk_all.isChecked()

    main_window.chk_all.setChecked(False)
    main_window.toggle_all_plugins()
    assert not any(w.checkbox.isChecked() for w in main_window.plugin_widgets)

    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)


def test_unchecking_single_plugin_unchecks_select_all(main_window):
    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()

    first = main_window.plugin_widgets[0]
    first.checkbox.setChecked(False)
    main_window.check_mutex_state()

    assert not main_window.chk_all.isChecked()


def test_run_without_path_shows_error_in_label(main_window):
    main_window.caminho_selecionado = None
    main_window.executar_plugin_run()
    assert "Please, select a path" in main_window.lbl_path.text()
    assert main_window.btn_run.isEnabled()


def test_run_without_any_plugin_selected_shows_error(main_window, tmp_path):
    main_window.caminho_selecionado = str(tmp_path)
    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(False)

    main_window.executar_plugin_run()
    assert "Please, select at least one plugin" in main_window.lbl_path.text()
    assert main_window.btn_run.isEnabled()


def test_on_analysis_finished_enables_report_and_eyes(main_window, tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(True)

    main_window.on_analysis_finished(results_dir)

    assert main_window.results_dir == results_dir
    assert main_window.btn_run.isEnabled()
    assert main_window.btn_report.isEnabled()

    for w in main_window.plugin_widgets:
        assert w.btn_eye.isEnabled()


def test_export_without_running_analysis_shows_message(main_window):
    if hasattr(main_window, "results_dir"):
        delattr(main_window, "results_dir")

    main_window.executar_plugin_export()
    assert "Run analysis first" in main_window.lbl_path.text()