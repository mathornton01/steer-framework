# =================================================================================================
# theme.py — Dark theme for STEER GUI
# =================================================================================================

# Color palette (derived from STEER branding)
COLORS = {
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
    "success": "#4caf50",
    "failure": "#ef5350",
    "warning": "#ffa726",
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}}

QLabel {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    padding: 0px;
}}

QLabel#sectionHeader {{
    font-size: 11pt;
    font-weight: bold;
    color: {COLORS['accent_light']};
    padding: 4px 0px;
}}

QLabel#statusLabel {{
    color: {COLORS['text_secondary']};
    font-size: 9pt;
}}

QPushButton {{
    background-color: {COLORS['btn_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['btn_border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: #545c6c;
    border-color: {COLORS['accent_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent_light']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}

QPushButton#runButton {{
    background-color: {COLORS['accent']};
    color: white;
    font-size: 11pt;
    font-weight: bold;
    padding: 10px 24px;
    border: 2px solid {COLORS['accent_light']};
    border-radius: 6px;
    min-height: 28px;
}}

QPushButton#runButton:hover {{
    background-color: {COLORS['accent_light']};
    border-color: #6a9ad5;
}}

QPushButton#runButton:pressed {{
    background-color: #2a5590;
}}

QPushButton#runButton:disabled {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}

QPushButton#stopButton {{
    background-color: {COLORS['failure']};
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
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_highlight']};
}}

QLineEdit:read-only {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
}}

QComboBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent']};
    selection-color: white;
    outline: none;
}}

QTreeWidget {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {COLORS['bg_tertiary']};
}}

QTreeWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QTreeWidget::item:hover {{
    background-color: {COLORS['bg_tertiary']};
}}

QTreeWidget::item:selected {{
    background-color: {COLORS['accent']};
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
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px 10px;
    font-weight: bold;
    font-size: 9pt;
}}

QTabWidget::pane {{
    background-color: {COLORS['bg_secondary']};
    border: none;
    border-top: 1px solid {COLORS['border']};
    top: 0px;
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 18px;
    margin-right: 0px;
    font-weight: 500;
    font-size: 9pt;
}}

QTabBar::tab:selected {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    border-bottom: 2px solid {COLORS['accent_highlight']};
}}

QTabBar::tab:hover:!selected {{
    color: {COLORS['text_secondary']};
    border-bottom: 2px solid {COLORS['border']};
}}

QProgressBar {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text_primary']};
    font-weight: bold;
    min-height: 20px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_light']});
    border-radius: 3px;
}}

QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 9pt;
    selection-background-color: {COLORS['accent']};
}}

QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    color: {COLORS['accent_light']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 12px;
    color: {COLORS['accent_light']};
}}

QGroupBox QPushButton {{
    background-color: {COLORS['btn_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['btn_border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QGroupBox QPushButton:hover {{
    background-color: #545c6c;
    border-color: {COLORS['accent_light']};
}}

QGroupBox QPushButton:pressed {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent_light']};
}}

QCheckBox {{
    spacing: 8px;
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['border_light']};
    border-radius: 3px;
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_light']};
}}

QSplitter::handle {{
    background-color: {COLORS['border']};
    width: 2px;
    margin: 0px 4px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_primary']};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_light']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_primary']};
    height: 10px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_light']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_tertiary']};
}}

QMenu {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent']};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 4px 8px;
}}

QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 9pt;
}}

QToolTip {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    font-size: 9pt;
}}

QListWidget {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {COLORS['bg_tertiary']};
}}

QListWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_tertiary']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['accent']};
    color: white;
}}

QListView {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    outline: none;
    alternate-background-color: {COLORS['bg_tertiary']};
}}

QListView::item {{
    padding: 4px 8px;
    border: none;
}}

QListView::item:hover {{
    background-color: {COLORS['bg_tertiary']};
}}

QListView::item:selected {{
    background-color: {COLORS['accent']};
    color: white;
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['accent_highlight']};
}}
"""
