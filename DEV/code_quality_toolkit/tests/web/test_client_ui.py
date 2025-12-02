from __future__ import annotations
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication
from web.client import MainWindow, _to_snake_case, AnalysisWorker
from web import client

# --------------------

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

    Evita threads, requests e I/O.
    Apenas guarda os argumentos e expõe finished/error com .connect()
    e .start() compatíveis.
    """

    def __init__(self, target_path, payload, api_url) -> None:
        self.target_path = Path(target_path)
        self.payload = payload
        self.api_url = api_url
        self.finished = DummySignal()
        self.error = DummySignal()

    def start(self) -> None:
        # Não faz nada – nos testes chamamos on_analysis_finished/error manualmente
        pass


@pytest.fixture
def main_window(app, monkeypatch):
    """
    Cria a MainWindow num estado controlado:

    - HAS_WEBENGINE = False  → usa QLabel no lugar de QWebEngineView.
    - requests.get mocado    → não chama backend real.
    - AnalysisWorker dummy   → não cria thread nem faz requests.
    """
    # 1) Desativa WebEngine para não depender de QWebEngine em CI
    monkeypatch.setattr(client, "HAS_WEBENGINE", False, raising=False)

    # 2) Finge API /plugins/configs a devolver 2 plugins com configs simples
    fake_plugins = {
        "StyleChecker": {"max_line_length": 88},
        "CyclomaticComplexity": {"max_complexity": 10},
    }

    def fake_get(url, *_, **__):
        # Garante que estamos a chamar o endpoint certo
        assert url.endswith("/plugins/configs")
        return DummyResponse(fake_plugins)

    monkeypatch.setattr(client.requests, "get", fake_get)

    # 3) Substitui AnalysisWorker por DummyWorker (sem threads)
    monkeypatch.setattr(client, "AnalysisWorker", DummyWorker)

    # 4) Cria janela principal normalmente
    win = client.MainWindow()

    # Garante que os plugins foram carregados do "backend" falso
    assert len(win.plugin_widgets) == 2
    return win


# ---------- TESTES DE UI / LÓGICA DE ESTADO ----------

def test_select_all_checks_and_unchecks_individual(main_window):
    """
    Cenário:
      - 'Select All' marcado → todos plugins marcados.
      - Desmarcar 'Select All' → todos desmarcados.
      - Voltar a marcar 'Select All' → todos marcados de novo.
    """
    # Estado inicial: todos selecionados
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)
    assert main_window.chk_all.isChecked()

    # Desmarca "Select All" → todos devem ser desmarcados
    main_window.chk_all.setChecked(False)
    main_window.toggle_all_plugins()
    assert not any(w.checkbox.isChecked() for w in main_window.plugin_widgets)

    # Marca "Select All" → todos devem ser marcados
    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()
    assert all(w.checkbox.isChecked() for w in main_window.plugin_widgets)


def test_unchecking_single_plugin_unchecks_select_all(main_window):
    """
    Cenário:
      - Todos marcados.
      - Desmarco apenas um plugin.
      - Mutex: 'Select All' deve ficar desmarcado.
    """
    main_window.chk_all.setChecked(True)
    main_window.toggle_all_plugins()

    # Desmarca apenas um plugin
    first = main_window.plugin_widgets[0]
    first.checkbox.setChecked(False)

    # Atualiza estado do 'Select All'
    main_window.check_mutex_state()

    assert not main_window.chk_all.isChecked()


def test_run_without_path_shows_error_in_label(main_window):
    """
    Cenário:
      - Nenhum ficheiro/pasta selecionado.
      - Clica em RUN → deve ver mensagem de erro no label,
        e o botão RUN continua ativo (worker nunca é criado).
    """
    main_window.caminho_selecionado = None

    main_window.executar_plugin_run()

    assert "Please, select a path" in main_window.lbl_path.text()
    assert main_window.btn_run.isEnabled()


def test_run_without_any_plugin_selected_shows_error(main_window, tmp_path):
    """
    Cenário:
      - Caminho válido selecionado.
      - Todos os checkboxes de plugins desmarcados.
      - Clica em RUN → deve aparecer mensagem 'select at least one plugin'
        e não deve criar worker.
    """
    main_window.caminho_selecionado = str(tmp_path)

    # Desmarca todos os plugins
    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(False)

    main_window.executar_plugin_run()

    assert "Please, select at least one plugin" in main_window.lbl_path.text()
    assert main_window.btn_run.isEnabled()


def test_on_analysis_finished_enables_report_and_eyes(main_window, tmp_path):
    """
    Cenário:
      - Simula fim de análise com um diretório de resultados.
      - Deve:
        - Guardar results_dir;
        - Reabilitar botão RUN;
        - Ativar botão SHOW REPORT;
        - Ativar 'eye' para plugins selecionados.
    """
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Garante que todos estão marcados antes
    for w in main_window.plugin_widgets:
        w.checkbox.setChecked(True)
        assert not w.btn_eye.isEnabled()

    main_window.on_analysis_finished(results_dir)

    assert main_window.results_dir == results_dir
    assert main_window.btn_run.isEnabled()
    assert main_window.btn_run.text() == "RUN"
    assert main_window.btn_report.isEnabled()

    for w in main_window.plugin_widgets:
        assert w.btn_eye.isEnabled()
        assert w.btn_eye.text() in ("👁", "⊘")


def test_export_without_running_analysis_shows_message(main_window):
    """
    Cenário:
      - Nenhuma análise foi feita (sem results_dir).
      - Clica em EXPORT → label deve indicar que é preciso fazer run primeiro.
    """
    if hasattr(main_window, "results_dir"):
        delattr(main_window, "results_dir")

    main_window.executar_plugin_export()

    assert "Run analysis first" in main_window.lbl_path.text()
