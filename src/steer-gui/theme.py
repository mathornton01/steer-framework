# =================================================================================================
# theme.py — Dark / Light theme for STEER GUI
# =================================================================================================

DARK_COLORS = {
    "bg_primary": "#1a1d23",
    "bg_secondary": "#22262e",
    "bg_tertiary": "#2a2f3a",
    "bg_input": "#181b20",
    "accent": "#3468a8",
    "accent_light": "#4a7ec5",
    "accent_highlight": "#e87722",
    "text_primary": "#e8eaed",
    "text_secondary": "#9aa0a8",
    "text_muted": "#727a85",
    "border": "#3e4451",
    "border_light": "#525968",
    "btn_bg": "#464d5a",
    "btn_border": "#6b7385",
    "btn_hover": "#545c6c",
    "success": "#4caf50",
    "failure": "#ef5350",
    "warning": "#ffa726",
}

LIGHT_COLORS = {
    "bg_primary": "#f0f1f4",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#e6e8ec",
    "bg_input": "#ffffff",
    "accent": "#2a5899",
    "accent_light": "#3a6db5",
    "accent_highlight": "#d06820",
    "text_primary": "#1e2028",
    "text_secondary": "#50555e",
    "text_muted": "#8a8f98",
    "border": "#c8ccd4",
    "border_light": "#b0b5be",
    "btn_bg": "#dde0e5",
    "btn_border": "#b0b5be",
    "btn_hover": "#cdd1d8",
    "success": "#388e3c",
    "failure": "#d32f2f",
    "warning": "#f57c00",
}

# Active color palette — starts as dark
COLORS: dict[str, str] = dict(DARK_COLORS)

_current_mode = "dark"


def current_mode() -> str:
    return _current_mode


def set_mode(mode: str) -> None:
    """Switch the active COLORS dict and rebuild STYLESHEET. mode = 'dark' | 'light'."""
    global _current_mode, STYLESHEET
    _current_mode = mode
    src = DARK_COLORS if mode == "dark" else LIGHT_COLORS
    COLORS.update(src)
    STYLESHEET = _build_stylesheet(COLORS)


def _build_stylesheet(c: dict[str, str]) -> str:
    return f"""
QMainWindow {{
    background-color: {c['bg_primary']};
    color: {c['text_primary']};
}}

QWidget {{
    background-color: {c['bg_primary']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}}

QLabel {{
    background-color: transparent;
    color: {c['text_primary']};
    padding: 0px;
}}

QLabel#sectionHeader {{
    font-size: 11pt;
    font-weight: bold;
    color: {c['accent_light']};
    padding: 4px 0px;
}}

QLabel#statusLabel {{
    color: {c['text_secondary']};
    font-size: 9pt;
}}

QPushButton {{
    background-color: {c['btn_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['btn_border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {c['btn_hover']};
    border-color: {c['accent_light']};
}}

QPushButton:pressed {{
    background-color: {c['accent']};
    border-color: {c['accent_light']};
}}

QPushButton:disabled {{
    background-color: {c['bg_tertiary']};
    color: {c['text_muted']};
    border-color: {c['border']};
}}

QPushButton#runButton {{
    background-color: {c['accent']};
    color: white;
    font-size: 11pt;
    font-weight: bold;
    padding: 10px 24px;
    border: 2px solid {c['accent_light']};
    border-radius: 6px;
    min-height: 28px;
}}

QPushButton#runButton:hover {{
    background-color: {c['accent_light']};
    border-color: #6a9ad5;
}}

QPushButton#runButton:pressed {{
    background-color: #2a5590;
}}

QPushButton#runButton:disabled {{
    background-color: {c['bg_tertiary']};
    color: {c['text_muted']};
    border-color: {c['border']};
}}

QPushButton#stopButton {{
    background-color: {c['failure']};
    color: white;
    font-weight: bold;
    border: 2px solid #f77c7a;
    border-radius: 6px;
    padding: 10px 24px;
    min-height: 28px;
}}

QPushButton#stopButton:hover {{
    background-color: #f56e6b;
    border-color: #f9a0a0;
}}

QLineEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {c['accent']};
}}

QLineEdit:focus {{
    border-color: {c['accent_highlight']};
}}

QLineEdit:read-only {{
    background-color: {c['bg_secondary']};
    color: {c['text_secondary']};
}}

QComboBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {c['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {c['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent']};
    selection-color: white;
    outline: none;
}}

QTreeWidget {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {c['bg_tertiary']};
}}

QTreeWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QTreeWidget::item:hover {{
    background-color: {c['bg_tertiary']};
}}

QTreeWidget::item:selected {{
    background-color: {c['accent']};
    color: white;
}}

QTreeWidget::branch {{
    background-color: transparent;
}}

QTreeWidget::branch:has-children:closed {{
    border-image: none;
}}

QTreeWidget::branch:has-children:open {{
    border-image: none;
}}

QHeaderView::section {{
    background-color: {c['bg_tertiary']};
    color: {c['text_secondary']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 6px 10px;
    font-weight: bold;
    font-size: 9pt;
}}

QTabWidget::pane {{
    background-color: {c['bg_secondary']};
    border: none;
    border-top: 1px solid {c['border']};
    top: 0px;
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c['text_muted']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 18px;
    margin-right: 0px;
    font-weight: 500;
    font-size: 9pt;
}}

QTabBar::tab:selected {{
    background-color: transparent;
    color: {c['text_primary']};
    border-bottom: 2px solid {c['accent_highlight']};
}}

QTabBar::tab:hover:!selected {{
    color: {c['text_secondary']};
    border-bottom: 2px solid {c['border']};
}}

QProgressBar {{
    background-color: {c['bg_input']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    text-align: center;
    color: {c['text_primary']};
    font-weight: bold;
    min-height: 20px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent']}, stop:1 {c['accent_light']});
    border-radius: 3px;
}}

QTextEdit, QPlainTextEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 8px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 9pt;
    selection-background-color: {c['accent']};
}}

QGroupBox {{
    background-color: {c['bg_secondary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    color: {c['accent_light']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 12px;
    color: {c['accent_light']};
}}

QGroupBox QPushButton {{
    background-color: {c['btn_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['btn_border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QGroupBox QPushButton:hover {{
    background-color: {c['btn_hover']};
    border-color: {c['accent_light']};
}}

QGroupBox QPushButton:pressed {{
    background-color: {c['accent']};
    border-color: {c['accent_light']};
}}

QCheckBox {{
    spacing: 8px;
    color: {c['text_primary']};
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {c['border_light']};
    border-radius: 3px;
    background-color: {c['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {c['accent']};
    border-color: {c['accent']};
}}

QCheckBox::indicator:hover {{
    border-color: {c['accent_light']};
}}

QSplitter::handle {{
    background-color: {c['border']};
    width: 2px;
    margin: 0px 4px;
}}

QSplitter::handle:hover {{
    background-color: {c['accent']};
}}

QScrollBar:vertical {{
    background-color: {c['bg_primary']};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {c['border_light']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {c['bg_primary']};
    height: 10px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['border_light']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QMenuBar {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border-bottom: 1px solid {c['border']};
    padding: 2px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {c['bg_tertiary']};
}}

QMenu {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {c['accent']};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background-color: {c['border']};
    margin: 4px 8px;
}}

QStatusBar {{
    background-color: {c['bg_secondary']};
    color: {c['text_secondary']};
    border-top: 1px solid {c['border']};
    font-size: 9pt;
}}

QToolTip {{
    background-color: {c['bg_tertiary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px;
    font-size: 9pt;
}}

QListWidget {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {c['bg_tertiary']};
}}

QListWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QListWidget::item:hover {{
    background-color: {c['bg_tertiary']};
}}

QListWidget::item:selected {{
    background-color: {c['accent']};
    color: white;
}}

QListView {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {c['bg_tertiary']};
}}

QListView::item {{
    padding: 4px 8px;
    border: none;
}}

QListView::item:hover {{
    background-color: {c['bg_tertiary']};
}}

QListView::item:selected {{
    background-color: {c['accent']};
    color: white;
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c['accent_highlight']};
}}
"""


# Initialize the default stylesheet
STYLESHEET = _build_stylesheet(COLORS)
