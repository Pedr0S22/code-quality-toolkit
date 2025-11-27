import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                            QFileDialog, QFrame)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Quality Toolkit App")
        
        # --- CONFIGURAÇÕES DE TAMANHO ---
        WINDOW_WIDTH = 1366
        WINDOW_HEIGHT = 768
        
        SIDEBAR_WIDTH = 300
        BOTTOM_HEIGHT = 80
        self.TOP_BAR_HEIGHT = 60 
        
        # CÁLCULO DO "TRUE" DASHBOARD SIZE
        self.DASH_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
        self.DASH_HEIGHT = WINDOW_HEIGHT - BOTTOM_HEIGHT - self.TOP_BAR_HEIGHT

        # BLOQUEAR O TAMANHO DA JANELA
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # --- ESTILO DARK MODE GLOBAL ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                color: #cccccc;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
        """)

        self.caminho_selecionado = None
        self.tipo_selecao = None
        self.is_dashboard_active = True

        # --- 2. ESTRUTURA PRINCIPAL ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # A. BARRA LATERAL ESQUERDA (PLUGINS)
        self.setup_sidebar(SIDEBAR_WIDTH, WINDOW_HEIGHT)

        # B. COLUNA DA DIREITA
        self.right_column = QWidget()
        self.right_column.setFixedSize(self.DASH_WIDTH, WINDOW_HEIGHT)
        # Fundo da área principal (Dark)
        self.right_column.setStyleSheet("background-color: #1e1e1e;")
        
        self.right_layout = QVBoxLayout(self.right_column)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        # B1. TOP BAR (Nova barra para o botão de alternar)
        self.setup_top_bar()

        # B2. CONTEÚDO (O Dashboard "Verdadeiro")
        self.setup_content_area()
        
        # B3. BARRA DE AÇÃO (Baixo)
        self.setup_action_bar(BOTTOM_HEIGHT)

        self.main_layout.addWidget(self.right_column)

    def setup_sidebar(self, width, height):
        self.sidebar = QFrame()
        self.sidebar.setFixedSize(width, height)
        # Sidebar com um tom ligeiramente diferente do fundo principal
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-right: 1px solid #333333;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Título PLUGINS
        lbl_titulo = QLabel("PLUGINS")
        lbl_titulo.setStyleSheet("color: #eff0f1; font-size: 22px; font-weight: bold; margin-top: 20px; letter-spacing: 1px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_titulo)
        
        # Exemplo de lista de plugins (decorativo)
        lbl_info = QLabel("Plugin A: Ready\nPlugin B: Ready")
        lbl_info.setStyleSheet("color: #6a6a6a; margin-top: 10px; font-size: 12px;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_info)

        sidebar_layout.addStretch()
        
        self.main_layout.addWidget(self.sidebar)

    def setup_top_bar(self):
        """Nova barra no topo apenas para alternar modos, fora do dashboard"""
        self.top_bar = QFrame()
        self.top_bar.setFixedSize(self.DASH_WIDTH, self.TOP_BAR_HEIGHT)
        self.top_bar.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #333333;")
        
        top_layout = QHBoxLayout(self.top_bar)
        # Margem esquerda de 20px para não colar totalmente à borda
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Botão Toggle ALINHADO À ESQUERDA (sem addStretch antes)
        self.btn_toggle = QPushButton("DASHBOARD")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        
        # Estilo Dark Mode Blue Accent
        btn_style = """
            QPushButton {
                padding: 6px 40px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 13px;
                border: 1px solid #3e3e42;
                background-color: #3e3e42;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #4e4e52;
            }
            /* Estado ATIVO (Dashboard ou Report) - Azul */
            QPushButton:checked {
                background-color: #007ACC;
                color: white;
                border: 1px solid #007ACC;
            }
        """
        self.btn_toggle.setStyleSheet(btn_style)
        self.btn_toggle.clicked.connect(self.alternar_visualizacao)
        
        top_layout.addWidget(self.btn_toggle)
        top_layout.addStretch() # Empurra tudo para a esquerda

        self.right_layout.addWidget(self.top_bar)

    def setup_content_area(self):
        self.content_area = QWidget()
        # Tamanho EXATO calculado
        self.content_area.setFixedSize(self.DASH_WIDTH, self.DASH_HEIGHT)
        self.content_area.setStyleSheet("background-color: #1e1e1e;")
        
        content_layout = QVBoxLayout(self.content_area)
        # REMOVIDAS AS MARGENS: O conteúdo toca nas bordas (0,0,0,0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- STACKED WIDGET (Ocupa todo o espaço restante) ---
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        
        # Página 1: Dashboard
        self.page_dashboard = QLabel(
            f"DASHBOARD AREA\n\nWidth: {self.DASH_WIDTH} px\nHeight: {self.DASH_HEIGHT} px",
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.page_dashboard.setStyleSheet("""
            background-color: #252526;
            color: #007ACC;
            font-size: 24px;
            font-weight: bold;
            border: none;
        """)
        
        # Página 2: Report
        self.page_report = QLabel("REPORT AREA", alignment=Qt.AlignmentFlag.AlignCenter)
        self.page_report.setStyleSheet("""
            background-color: #252526;
            color: #ce9178;
            font-size: 24px;
            font-weight: bold;
            border: none;
        """)

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_report)
        
        content_layout.addWidget(self.stack)
        self.right_layout.addWidget(self.content_area)

    def alternar_visualizacao(self, checked):
        self.is_dashboard_active = checked
        if self.is_dashboard_active:
            self.stack.setCurrentIndex(0)
            self.btn_toggle.setText("DASHBOARD")
        else:
            self.stack.setCurrentIndex(1)
            self.btn_toggle.setText("REPORT")

    def setup_action_bar(self, height):
        self.action_bar = QFrame()
        self.action_bar.setFixedSize(self.DASH_WIDTH, height)
        # Barra de baixo escura
        self.action_bar.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-top: 1px solid #333333;
            }
        """)
        
        bar_layout = QHBoxLayout(self.action_bar)
        bar_layout.setContentsMargins(30, 10, 30, 10)
        bar_layout.setSpacing(15)

        # Estilo botões secundários (Dark Mode)
        secondary_btn_style = """
            QPushButton {
                background-color: #3e3e42;
                color: #cccccc;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4e4e52;
                color: white;
            }
        """

        self.btn_file = QPushButton("Escolher Ficheiro")
        self.btn_folder = QPushButton("Escolher Pasta")
        self.btn_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_file.setStyleSheet(secondary_btn_style)
        self.btn_folder.setStyleSheet(secondary_btn_style)

        self.lbl_path = QLabel("Nenhum caminho selecionado")
        self.lbl_path.setStyleSheet("color: #858585; font-style: italic; margin-left: 5px; border: none;")

        self.btn_file.clicked.connect(self.selecionar_ficheiro)
        self.btn_folder.clicked.connect(self.selecionar_pasta)

        bar_layout.addWidget(self.btn_file)
        bar_layout.addWidget(self.btn_folder)
        bar_layout.addWidget(self.lbl_path)

        bar_layout.addStretch()

        # Botões de Ação Principal
        self.btn_run = QPushButton("RUN")
        self.btn_export = QPushButton("EXPORT")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)

        # RUN - Azul (Cor de ação principal)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                padding: 10px 25px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #0062a3; }
        """)

        # EXPORT - Cinza mais claro ou outra cor secundária
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #3e3e42;
                color: white;
                font-weight: bold;
                padding: 10px 25px;
                border-radius: 4px;
                border: 1px solid #555;
            }
            QPushButton:hover { background-color: #4e4e52; }
        """)

        self.btn_run.clicked.connect(self.executar_plugin_run)
        self.btn_export.clicked.connect(self.executar_plugin_export)

        # --- AQUI ESTÁ A TROCA ---
        # 1. Adiciona Export primeiro
        bar_layout.addWidget(self.btn_export)
        # 2. Adiciona Run depois
        bar_layout.addWidget(self.btn_run)

        self.right_layout.addWidget(self.action_bar)

    def selecionar_ficheiro(self):
        ficheiro, _ = QFileDialog.getOpenFileName(self, "Selecionar Ficheiro")
        if ficheiro:
            self.caminho_selecionado = ficheiro
            self.tipo_selecao = 'ficheiro'
            nome_ficheiro = ficheiro.split('/')[-1]
            self.lbl_path.setText(f"📄 {nome_ficheiro}")
            self.lbl_path.setStyleSheet("color: #cccccc; font-weight: bold; border: none;")

    def selecionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta:
            self.caminho_selecionado = pasta
            self.tipo_selecao = 'pasta'
            nome_pasta = pasta.split('/')[-1]
            self.lbl_path.setText(f"📂 {nome_pasta}")
            self.lbl_path.setStyleSheet("color: #cccccc; font-weight: bold; border: none;")

    def executar_plugin_run(self):
        modo = "DASHBOARD" if self.is_dashboard_active else "REPORT"
        if not self.caminho_selecionado:
            self.lbl_path.setText("⚠️ Selecione algo primeiro!")
            self.lbl_path.setStyleSheet("color: #f48771; font-weight: bold; border: none;")
            return
        print(f"--> RUN: {modo} | Caminho: {self.caminho_selecionado}")

    def executar_plugin_export(self):
        modo = "DASHBOARD" if self.is_dashboard_active else "REPORT"
        print(f"--> EXPORT: {modo}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    
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
