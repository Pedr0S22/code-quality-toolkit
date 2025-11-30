import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                            QFileDialog, QFrame, QCheckBox, QScrollArea,
                            QLineEdit, QFormLayout)
from PyQt6.QtCore import Qt, QUrl

# --- WEB ENGINE CHECK (Required for D3.js/HTML Rendering) ---
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    print("WARNING: PyQt6-WebEngine not installed. Run 'pip install PyQt6-WebEngine'")

# --- MOCK API RESPONSE (Simulating GET /api/v1/plugins/configs) ---
def mock_fetch_plugins():
    return {
        "CyclomaticComplexity": {
            "enabled": True,
            "threshold": 10,
            "exclude_tests": True
        },
        "DuplicationHunter": {
            "enabled": True,
            "min_lines": 5,
            "ignore_imports": False
        },
        "DeadCodeFinder": {
            "enabled": True,
            "deep_scan": True
        },
        "SecurityScanner": {
            "enabled": True,
            "level": "high"
        },
        "StyleChecker": {
            "enabled": True,
            "standard": "pep8"
        },
        "DependencyGraph": {
            "enabled": True,
            "depth": 3
        }
    }

# --- CUSTOM PLUGIN WIDGET ---
class PluginItemWidget(QWidget):
    """
    Represents a single plugin row in the sidebar.
    Includes: Checkbox, Name, Eye Icon, Expand Toggle, and Config Form.
    """
    def __init__(self, name, config, parent_controller):
        super().__init__()
        self.name = name
        self.default_config = config
        self.controller = parent_controller # Reference to MainWindow for callbacks
        self.inputs = {} # Store input fields to retrieve values later

        # Main Layout (Vertical: Header Row + Config Container)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(0)

        # --- 1. HEADER ROW ---
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True) # Default checked
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

        # --- FIX: Custom Style to ensure checkbox is visible in Dark Mode ---
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #555; border-radius: 3px;
                background: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background: #007ACC;
                border: 1px solid #AAAAAA; /* grey frame when selected */
            }
            QCheckBox::indicator:hover { border: 1px solid #007ACC; }
        """)
        
        # Name Label
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("color: #eff0f1; font-weight: bold; border: none;")
        
        # Eye Button - Start with "Closed" icon (⊘)
        self.btn_eye = QPushButton("⊘")
        self.btn_eye.setFixedSize(30, 25)
        self.btn_eye.setEnabled(False)
        
        # Expand/Collapse Button (v / ^)
        self.btn_expand = QPushButton("v")
        self.btn_expand.setFixedSize(25, 25)
        self.btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expand.setCheckable(True)
        self.btn_expand.setStyleSheet("""
            QPushButton { background: transparent; color: #ccc; border: none; font-weight: bold; font-family: monospace; }
            QPushButton:hover { background-color: #3e3e42; border-radius: 3px; }
            QPushButton:checked { color: #007ACC; }
        """)
        self.btn_expand.clicked.connect(self.toggle_config_visibility)

        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.lbl_name)
        self.header_layout.addStretch() # Spacer
        self.header_layout.addWidget(self.btn_eye)
        self.header_layout.addWidget(self.btn_expand)

        # --- 2. CONFIG CONTAINER (Hidden by default) ---
        self.config_container = QFrame()
        self.config_container.setVisible(False)
        # Visual indentation for hierarchy
        self.config_container.setStyleSheet("""
            QFrame { background-color: #1e1e1e; border-left: 2px solid #333; margin-left: 20px; margin-right: 10px; }
            QLabel { border: none; }
        """)
        
        self.form_layout = QFormLayout(self.config_container)
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        self.form_layout.setVerticalSpacing(10)

        # Dynamically create inputs based on default config keys
        for key, value in config.items():
            if key == "enabled": continue # Skip internal flags if desired

            lbl = QLabel(f"{key}:")
            lbl.setStyleSheet("color: #aaa; font-size: 12px;")
            
            inp = QLineEdit(str(value))
            inp.setStyleSheet("background-color: #2d2d30; color: #ddd; border: 1px solid #3e3e42; border-radius: 2px; padding: 4px;")
            
            self.form_layout.addRow(lbl, inp)
            self.inputs[key] = inp

        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.config_container)

    def toggle_config_visibility(self, checked):
        self.config_container.setVisible(checked)
        self.btn_expand.setText("∧" if checked else "v")

    def on_checkbox_changed(self, state):
        # Notify the sidebar controller to check if "Select All" needs updating
        self.controller.check_mutex_state()

    def get_config(self):
        """Returns the current config values from inputs"""
        cfg = {}
        for k, inp in self.inputs.items():
            cfg[k] = inp.text() # Retrieve user edited text
        return cfg
    
    def set_dashboard_status(self, active: bool):
        """Helper to switch icon and state simultaneously"""
        self.btn_eye.setEnabled(active)
        # 👁 = Open/Active, ⊘ = Closed/Inactive
        self.btn_eye.setText("👁" if active else "⊘")
        self.btn_eye.setCursor(Qt.CursorShape.PointingHandCursor)

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Quality Toolkit App")
        
        # --- SIZE CONFIG ---
        WINDOW_WIDTH = 1366
        WINDOW_HEIGHT = 768
        SIDEBAR_WIDTH = 340 # Slightly wider for scrollbar
        BOTTOM_HEIGHT = 80
        self.TOP_BAR_HEIGHT = 60
        
        self.DASH_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
        self.DASH_HEIGHT = WINDOW_HEIGHT - BOTTOM_HEIGHT - self.TOP_BAR_HEIGHT

        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # --- GLOBAL STYLE ---
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { font-family: 'Segoe UI', sans-serif; color: #cccccc; }
            QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            /* Scrollbar Styling */
            QScrollBar:vertical { border: none; background: #252526; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.caminho_selecionado = None
        self.is_dashboard_active = True
        self.plugin_widgets = [] # Keep track of plugin instances

        # --- MAIN STRUCTURE ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # A. SIDEBAR (PLUGINS)
        self.setup_sidebar(SIDEBAR_WIDTH, WINDOW_HEIGHT)

        # B. RIGHT COLUMN
        self.right_column = QWidget()
        self.right_column.setFixedSize(self.DASH_WIDTH, WINDOW_HEIGHT)
        self.right_column.setStyleSheet("background-color: #1e1e1e;")
        
        self.right_layout = QVBoxLayout(self.right_column)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        # B1. Top Bar
        self.setup_top_bar()
        # B2. Content (Dashboard/Report)
        self.setup_content_area()
        # B3. Action Bar
        self.setup_action_bar(BOTTOM_HEIGHT)

        self.main_layout.addWidget(self.right_column)
        
        # Load Plugins immediately (Simulating API Call on startup)
        self.load_plugins()

    def setup_sidebar(self, width, height):
        self.sidebar = QFrame()
        self.sidebar.setFixedSize(width, height)
        self.sidebar.setStyleSheet("background-color: #252526; border-right: 1px solid #333333;")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        lbl_titulo = QLabel("PLUGINS")
        lbl_titulo.setStyleSheet("color: #eff0f1; font-size: 22px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; letter-spacing: 1px; border: none;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_titulo)
        
        # "Select All" Container
        self.chk_all_container = QFrame()
        self.chk_all_container.setStyleSheet("background-color: #2d2d30; padding: 10px; border-bottom: 1px solid #3e3e42;")
        chk_layout = QHBoxLayout(self.chk_all_container)
        chk_layout.setContentsMargins(10, 0, 0, 0)
        
        self.chk_all = QCheckBox("Select All")
        self.chk_all.setChecked(True)
        self.chk_all.setCursor(Qt.CursorShape.PointingHandCursor)
        # Apply the same indicator style here so it doesn't disappear
        self.chk_all.setStyleSheet("""
            QCheckBox {
                color: #fff; font-weight: bold; font-size: 14px;
            }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #555; border-radius: 3px;
                background: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background: #007ACC;
                border: 1px solid #AAAAAA; /* grey frame */
            }
            QCheckBox::indicator:hover { border: 1px solid #007ACC; }
        """)
        self.chk_all.clicked.connect(self.toggle_all_plugins)
        
        chk_layout.addWidget(self.chk_all)
        sidebar_layout.addWidget(self.chk_all_container)

        # Scroll Area for Plugins List
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setContentsMargins(5, 5, 5, 5)
        self.plugins_layout.setSpacing(2)
        self.plugins_layout.addStretch() # Push items up
        
        self.scroll_area.setWidget(self.plugins_container)
        sidebar_layout.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(self.sidebar)

    def load_plugins(self):
        """Fetches plugins from (mock) API and populates the sidebar"""
        data = mock_fetch_plugins()
        
        # Remove the stretch item temporarily to add widgets
        self.plugins_layout.takeAt(self.plugins_layout.count() - 1)

        for name, config in data.items():
            # Create Custom Widget
            widget = PluginItemWidget(name, config, self)
            
            # Connect the Eye button to the main window handler
            # using lambda to capture the specific name
            widget.btn_eye.clicked.connect(lambda checked, n=name: self.show_plugin_dashboard(n))
            
            self.plugins_layout.addWidget(widget)
            self.plugin_widgets.append(widget)

        self.plugins_layout.addStretch() # Re-add stretch

    # --- MUTEX LOGIC (Select All vs Individual) ---
    def toggle_all_plugins(self):
        """If All checked -> Check all items. If Unchecked -> Uncheck all items."""
        state = self.chk_all.isChecked()
        for widget in self.plugin_widgets:
            # blockSignals prevents recursion loop
            widget.checkbox.blockSignals(True)
            widget.checkbox.setChecked(state)
            widget.checkbox.blockSignals(False)

    def check_mutex_state(self):
        """Called when a child is clicked. Updates 'All' checkbox."""
        all_checked = all(w.checkbox.isChecked() for w in self.plugin_widgets)
        self.chk_all.blockSignals(True)
        self.chk_all.setChecked(all_checked)
        self.chk_all.blockSignals(False)

    def setup_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setFixedSize(self.DASH_WIDTH, self.TOP_BAR_HEIGHT)
        self.top_bar.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #333333;")
        
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        self.btn_toggle = QPushButton("DASHBOARD")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        
        btn_style = """
            QPushButton {
                padding: 6px 40px; font-weight: bold; border-radius: 4px; font-size: 13px;
                border: 1px solid #3e3e42; background-color: #3e3e42; color: #cccccc;
            }
            QPushButton:hover { background-color: #4e4e52; }
            QPushButton:checked { background-color: #007ACC; color: white; border: 1px solid #007ACC; }
        """
        self.btn_toggle.setStyleSheet(btn_style)
        self.btn_toggle.clicked.connect(self.alternar_visualizacao)
        
        top_layout.addWidget(self.btn_toggle)
        top_layout.addStretch()
        self.right_layout.addWidget(self.top_bar)

    def setup_content_area(self):
        self.content_area = QWidget()
        self.content_area.setFixedSize(self.DASH_WIDTH, self.DASH_HEIGHT)
        self.content_area.setStyleSheet("background-color: #1e1e1e;")
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        
        # PAGE 0: DASHBOARD (Using WebEngine for HTML/D3.js)
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            self.web_view.setStyleSheet("background-color: #1e1e1e;")
            
            # Placeholder HTML
            default_html = """
            <html>
            <body style='background-color:#1e1e1e; color:#555; font-family:sans-serif;
                        display:flex; justify-content:center; align-items:center; height:100%; overflow:hidden;'>
                <div style='text-align:center;'>
                    <h1 style='font-size:40px; margin-bottom:10px;'>Ready to Analyze</h1>
                    <p>Select plugins on the left and click RUN</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(default_html)
            self.stack.addWidget(self.web_view)
        else:
            # Fallback if library missing
            self.web_view = QLabel("Error: PyQt6-WebEngine is missing.\nCannot render Dashboards.",
                                alignment=Qt.AlignmentFlag.AlignCenter)
            self.stack.addWidget(self.web_view)
        
        # PAGE 1: REPORT
        self.page_report = QLabel("REPORT AREA (JSON/Text Data)", alignment=Qt.AlignmentFlag.AlignCenter)
        self.page_report.setStyleSheet("background-color: #1e1e1e; color: #ce9178; font-size: 24px; font-weight: bold;")
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
        self.action_bar.setStyleSheet("background-color: #252526; border-top: 1px solid #333333;")
        
        bar_layout = QHBoxLayout(self.action_bar)
        bar_layout.setContentsMargins(30, 10, 30, 10)
        bar_layout.setSpacing(15)

        secondary_btn_style = """
            QPushButton { background-color: #3e3e42; color: #cccccc; border: 1px solid #3e3e42; border-radius: 4px; padding: 8px 15px; font-weight: 600; }
            QPushButton:hover { background-color: #4e4e52; color: white; }
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

        self.btn_export = QPushButton("EXPORT")
        self.btn_run = QPushButton("RUN")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #007ACC; color: white; font-weight: bold; padding: 10px 25px; border-radius: 4px; border: none; }
            QPushButton:hover { background-color: #0062a3; }
        """)
        self.btn_export.setStyleSheet(secondary_btn_style)

        self.btn_run.clicked.connect(self.executar_plugin_run)
        self.btn_export.clicked.connect(self.executar_plugin_export)

        bar_layout.addWidget(self.btn_export)
        bar_layout.addWidget(self.btn_run)

        self.right_layout.addWidget(self.action_bar)

    def selecionar_ficheiro(self):
        ficheiro, _ = QFileDialog.getOpenFileName(self, "Selecionar Ficheiro")
        if ficheiro:
            self.caminho_selecionado = ficheiro
            self.lbl_path.setText(f"📄 {ficheiro.split('/')[-1]}")
            self.lbl_path.setStyleSheet("color: #cccccc; font-weight: bold; border: none;")

    def selecionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta:
            self.caminho_selecionado = pasta
            self.lbl_path.setText(f"📂 {pasta.split('/')[-1]}")
            self.lbl_path.setStyleSheet("color: #cccccc; font-weight: bold; border: none;")

    def executar_plugin_run(self):
        """Logic: Gather Configs -> Send to API (simulated) -> Unlock Dashboards"""
        if not self.caminho_selecionado:
            self.lbl_path.setText("⚠️ Selecione algo primeiro!")
            self.lbl_path.setStyleSheet("color: #f48771; font-weight: bold; border: none;")
            return

        # 1. GATHER DATA FROM PLUGINS
        selected_payload = {}
        any_selected = False

        for widget in self.plugin_widgets:
            if widget.checkbox.isChecked():
                any_selected = True
                # Get the config (updated by user)
                selected_payload[widget.name] = widget.get_config()

        if not any_selected:
            self.lbl_path.setText("⚠️ Selecione pelo menos um plugin!")
            return

        print("--- RUNNING ANALYSIS ---")
        print(f"Target: {self.caminho_selecionado}")
        print("Payload (Plugins + Configs):")
        print(json.dumps(selected_payload, indent=2))
        
        # 2. SIMULATE COMPLETION
        # Logic: Analysis finished -> Toggle Eye Icon and Enable Button
        for widget in self.plugin_widgets:
            # If checked, set to Active (Open Eye), else Inactive (Closed Eye)
            is_active = widget.checkbox.isChecked()
            widget.set_dashboard_status(is_active)
        
        # Switch to dashboard view automatically
        self.stack.setCurrentIndex(0)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setText("DASHBOARD")
        
        if HAS_WEBENGINE:
            # Show success message in WebEngine
            self.web_view.setHtml("""
                <body style='background-color:#1e1e1e; font-family:Segoe UI, sans-serif; display:flex; justify-content:center; align-items:center; height:100%;'>
                    <h2 style='color:#007ACC;'>Analysis Complete! <br><span style='color:#777; font-size:18px'>Click an eye icon 👁 to view specific results.</span></h2>
                </body>
            """)

    def show_plugin_dashboard(self, plugin_name):
        """
        Called when the Eye icon is clicked.
        Checks for a dashboard file (simulated) and loads it.
        """
        if not HAS_WEBENGINE:
            return

        print(f"--> Loading Dashboard: {plugin_name}")
        
        # Switch to dashboard page
        self.stack.setCurrentIndex(0)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setText("DASHBOARD")

        # SIMULATE D3.js/HTML CONTENT
        # In a real app, you would do: self.web_view.setUrl(QUrl.fromLocalFile("/path/to/dashboard.html"))
        
        # Here we inject HTML/CSS/SVG directly to demonstrate it works
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ background-color: #1e1e1e; color: #ccc; font-family: 'Segoe UI', sans-serif; padding: 20px; }}
                h1 {{ color: #007ACC; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                .card {{ background: #252526; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #333; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                .metric {{ font-size: 24px; font-weight: bold; color: #fff; }}
                .label {{ color: #888; font-size: 14px; margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h1>{plugin_name} Dashboard</h1>
            
            <div class="card">
                <div class="label">Total Issues Found</div>
                <div class="metric">42</div>
            </div>

            <div class="card">
                <div class="label">Visualization (D3.js Simulation)</div>
                <svg width="100%" height="150" style="margin-top:15px">
                    <rect x="0" y="20" width="80%" height="30" fill="#333" rx="5" />
                    <rect x="0" y="20" width="45%" height="30" fill="#007ACC" rx="5" />
                    <text x="5" y="40" fill="white" font-size="12">Coverage: 45%</text>
                    
                    <circle cx="50" cy="100" r="20" fill="#ce9178" />
                    <circle cx="100" cy="100" r="15" fill="#4ec9b0" />
                    <circle cx="140" cy="100" r="10" fill="#dcdcaa" />
                </svg>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content)

    def executar_plugin_export(self):
        print("--> EXPORT clicked")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())