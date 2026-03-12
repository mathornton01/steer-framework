# =================================================================================================
# main_window.py — Frameless main window with custom title bar for STEER GUI
# =================================================================================================

import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QSettings, QPoint, QSize, QRectF
from PyQt6.QtGui import QAction, QPainter, QColor, QPainterPath, QPixmap, QFont, QRegion
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPlainTextEdit,
    QProgressBar, QPushButton, QSplitter, QSpinBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox,
    QSizePolicy, QApplication,
)

from theme import COLORS, set_mode, current_mode, THEMES, THEME_IDS
from test_registry import TestRegistry, SteerTestInfo
from test_runner import TestRunner
from report_viewer import ReportViewer, _nuanced_eval, _eval_badge
from docs_viewer import DocsViewer
from bit_array_dialog import BitArrayDialog

CORNER_RADIUS = 16

# Role for storing test info on tree items
TEST_INFO_ROLE = Qt.ItemDataRole.UserRole
PLAN_DATA_ROLE = Qt.ItemDataRole.UserRole + 1

# Editable test-specific parameters per test family.
# Maps program_name prefix → list of param dicts.
# "key" is the JSON parameter name the C code reads.
# "type" is "int" or "float".
TEST_EDITABLE_PARAMS: dict[str, list[dict]] = {
    # NIST STS tests with test-specific parameters
    "nist_sts_approximate_entropy": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 10, "min": 2, "max": 100},
    ],
    "nist_sts_block_frequency": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 128, "min": 20, "max": 100000},
    ],
    "nist_sts_linear_complexity": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 500, "min": 500, "max": 5000},
    ],
    "nist_sts_non_overlapping_template_matching": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 9, "min": 2, "max": 21},
    ],
    "nist_sts_overlapping_template_matching": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 9, "min": 2, "max": 21},
    ],
    "nist_sts_serial": [
        {"label": "Block len", "key": "block length", "type": "int", "default": 16, "min": 2, "max": 64},
    ],
    # TestU01 tests
    "testu01_serial_over": [
        {"label": "Dimension", "key": "dimension", "type": "int", "default": 2, "min": 2, "max": 4},
        {"label": "Bits/value", "key": "bits per value", "type": "int", "default": 4, "min": 2, "max": 8},
    ],
    "testu01_close_pairs": [
        {"label": "Points", "key": "num points", "type": "int", "default": 2000, "min": 100, "max": 50000},
        {"label": "Dimension", "key": "dimension", "type": "int", "default": 2, "min": 2, "max": 5},
    ],
    "testu01_collision_over": [
        {"label": "Bits/window", "key": "bits per window", "type": "int", "default": 10, "min": 5, "max": 20},
        {"label": "Num values", "key": "num values", "type": "int", "default": 10000, "min": 100, "max": 100000},
    ],
    "testu01_gcd": [
        {"label": "Num pairs", "key": "num pairs", "type": "int", "default": 10000, "min": 100, "max": 100000},
    ],
    "testu01_linear_complexity": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 5000, "min": 500, "max": 50000},
    ],
    "testu01_sum_collector": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 10, "min": 3, "max": 50},
    ],
    "testu01_savir2": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 30, "min": 5, "max": 200},
    ],
    "testu01_coupon_collector": [
        {"label": "Num coupons", "key": "num coupons", "type": "int", "default": 5, "min": 3, "max": 10},
    ],
    "testu01_weight_distribution": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 256, "min": 32, "max": 4096},
    ],
    "testu01_close_pairs_bit_match": [
        {"label": "Num bits", "key": "num bits", "type": "int", "default": 20, "min": 8, "max": 32},
    ],
    "testu01_simplified_poker": [
        {"label": "Hand size", "key": "hand size", "type": "int", "default": 5, "min": 3, "max": 10},
        {"label": "Categories", "key": "num categories", "type": "int", "default": 16, "min": 4, "max": 64},
    ],
    "testu01_gap": [
        {"label": "Lower (a)", "key": "gap alpha", "type": "float", "default": 0.0, "min": 0.0, "max": 0.9},
        {"label": "Upper (b)", "key": "gap beta", "type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
    ],
    "testu01_collision_permut": [
        {"label": "Tuple size", "key": "tuple size", "type": "int", "default": 10, "min": 3, "max": 20},
    ],
    "testu01_max_of_t": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 5, "min": 2, "max": 20},
        {"label": "Num bins", "key": "num bins", "type": "int", "default": 20, "min": 5, "max": 100},
    ],
    "testu01_run": [
        {"label": "Max run len", "key": "max run length", "type": "int", "default": 6, "min": 4, "max": 12},
    ],
    "testu01_permutation": [
        {"label": "Tuple size", "key": "tuple size", "type": "int", "default": 5, "min": 3, "max": 7},
    ],
    "testu01_sample_product": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 10, "min": 2, "max": 50},
    ],
    "testu01_sample_mean": [
        {"label": "Group size", "key": "group size", "type": "int", "default": 30, "min": 5, "max": 200},
    ],
    "testu01_random_walk": [
        {"label": "Walk len", "key": "walk length", "type": "int", "default": 1000, "min": 100, "max": 100000},
    ],
    "testu01_hamming_weight": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 32, "min": 8, "max": 256},
    ],
    "testu01_hamming_correlation": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 32, "min": 8, "max": 256},
    ],
    "testu01_hamming_independence": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 32, "min": 8, "max": 256},
    ],
    "testu01_string_run": [
        {"label": "Max run len", "key": "max run length", "type": "int", "default": 8, "min": 4, "max": 16},
    ],
    "testu01_autocorrelation": [
        {"label": "Lag", "key": "lag", "type": "int", "default": 1, "min": 1, "max": 100},
    ],
    "testu01_periods_in_strings": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 16, "min": 4, "max": 64},
    ],
    "testu01_longest_head_run": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 1000, "min": 100, "max": 100000},
    ],
    "testu01_entropy_discretization": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 8, "min": 2, "max": 16},
    ],
    "testu01_multinomial_bits_over": [
        {"label": "Tuple size", "key": "tuple size", "type": "int", "default": 4, "min": 2, "max": 10},
    ],
    # Diehard Marsaglia tests with test-specific params
    # (rank_32x32, rank_6x8, bitstream, opso, oqso, dna, count_1s_stream,
    #  count_1s_byte, sums, runs have no test-specific params)
    "diehard_3dsphere": [
        {"label": "Num points", "key": "num points", "type": "int", "default": 4000, "min": 100, "max": 50000},
    ],
    "diehard_craps": [
        {"label": "Num games", "key": "num games", "type": "int", "default": 200000, "min": 1000, "max": 1000000},
    ],
    "diehard_marsaglia_tsang_gcd": [
        {"label": "Num pairs", "key": "num pairs", "type": "int", "default": 10000, "min": 1000, "max": 10000000},
    ],
    # Dieharder DAB tests (David Bauer)
    # diehard_dab_bytedistrib has no test-specific params (standard 3 only)
    "diehard_dab_dct": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 256, "min": 64, "max": 4096},
    ],
    "diehard_dab_filltree": [
        {"label": "Tree depth", "key": "tree depth", "type": "int", "default": 15, "min": 5, "max": 32},
    ],
    "diehard_dab_filltree2": [
        {"label": "Tree depth", "key": "tree depth", "type": "int", "default": 15, "min": 5, "max": 32},
    ],
    "diehard_dab_monobit2": [
        {"label": "Block size", "key": "block size", "type": "int", "default": 4096, "min": 256, "max": 1048576},
    ],
    # Dieharder RGB tests (Robert G. Brown)
    "diehard_rgb_bitdist": [
        {"label": "N-tuple", "key": "ntuple", "type": "int", "default": 8, "min": 1, "max": 12},
    ],
    "diehard_rgb_minimum_distance": [
        {"label": "Dimension", "key": "dimension", "type": "int", "default": 2, "min": 2, "max": 5},
        {"label": "Num points", "key": "num points", "type": "int", "default": 4000, "min": 100, "max": 50000},
    ],
    "diehard_rgb_permutations": [
        {"label": "Tuple size", "key": "tuple size", "type": "int", "default": 5, "min": 2, "max": 10},
    ],
    "diehard_rgb_lagged_sum": [
        {"label": "Lag", "key": "lag", "type": "int", "default": 0, "min": 0, "max": 32},
    ],
    # diehard_rgb_kstest has no test-specific params (standard 3 only)
}


# =================================================================================================
#  Custom title bar widget
# =================================================================================================

class TitleBar(QWidget):
    """Custom title bar with window controls and dragging support."""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self._window = parent_window
        self._drag_pos = None
        self.setFixedHeight(44)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(0)

        # Logo icon (small)
        logo_path = Path(__file__).parent / "resources" / "steer-blue-logo.png"
        self.logo_label = QLabel()
        if logo_path.exists():
            pm = QPixmap(str(logo_path)).scaledToHeight(
                20, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pm)
        self.logo_label.setFixedWidth(pm.width() + 8 if not self.logo_label.pixmap().isNull() else 24)
        self.logo_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.logo_label)

        layout.addSpacing(8)

        # Title text
        self.title_label = QLabel("Anametric STEER")
        self.title_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 9pt; "
            f"font-weight: 500; background: transparent;"
        )
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Theme selector button (opens theme menu)
        self.theme_btn = QPushButton("🎨")
        self.theme_btn.setToolTip("Select theme")
        self.theme_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 8px; color: {COLORS['text_secondary']}; font-size: 13pt; "
            f"padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}"
        )
        self.theme_btn.clicked.connect(self._show_theme_menu)
        layout.addWidget(self.theme_btn)

        layout.addSpacing(4)

        # Window control buttons
        btn_style_base = (
            "QPushButton {{ background: transparent; border: none; "
            "border-radius: 8px; color: {color}; font-size: {size}; "
            "padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            "QPushButton:hover {{ background-color: {hover_bg}; }}"
        )

        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setStyleSheet(btn_style_base.format(
            color=COLORS["text_secondary"], size="12pt",
            hover_bg=COLORS["bg_tertiary"]
        ))
        self.minimize_btn.clicked.connect(self._window.showMinimized)
        layout.addWidget(self.minimize_btn)

        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setStyleSheet(btn_style_base.format(
            color=COLORS["text_secondary"], size="11pt",
            hover_bg=COLORS["bg_tertiary"]
        ))
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 8px; color: {COLORS['text_secondary']}; font-size: 10pt; "
            f"padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['failure']}; color: white; }}"
        )
        self.close_btn.clicked.connect(self._window.close)
        layout.addWidget(self.close_btn)

    def _toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def _show_theme_menu(self):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        for tid, name, _ in THEMES:
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(tid == current_mode())
            action.setData(tid)
            action.triggered.connect(lambda checked, t=tid: self._apply_theme(t))
        menu.exec(self.theme_btn.mapToGlobal(
            self.theme_btn.rect().bottomLeft()
        ))

    def _apply_theme(self, theme_id: str):
        set_mode(theme_id)
        from theme import STYLESHEET
        QApplication.instance().setStyleSheet(STYLESHEET)
        # Refresh inline styles that reference COLORS
        self._window.update_inline_styles()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._window.isMaximized():
                self._window.showNormal()
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self._toggle_maximize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLORS["bg_secondary"]))
        # Only round top corners
        path = QPainterPath()
        r = float(CORNER_RADIUS)
        w, h = float(self.width()), float(self.height())
        path.moveTo(0, h)
        path.lineTo(0, r)
        path.arcTo(QRectF(0, 0, 2 * r, 2 * r), 180, -90)
        path.lineTo(w - r, 0)
        path.arcTo(QRectF(w - 2 * r, 0, 2 * r, 2 * r), 90, -90)
        path.lineTo(w, h)
        path.closeSubpath()
        p.drawPath(path)

        # Bottom border line
        p.setPen(QColor(COLORS["border"]))
        p.drawLine(0, int(h) - 1, int(w), int(h) - 1)
        p.end()


# =================================================================================================
#  Resize grip for bottom-right corner
# =================================================================================================

class ResizeGrip(QWidget):
    """Invisible resize grip for the bottom-right corner."""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self._window = parent_window
        self._drag_pos = None
        self._drag_size = None
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_size = self._window.size()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            new_w = max(self._window.minimumWidth(), self._drag_size.width() + delta.x())
            new_h = max(self._window.minimumHeight(), self._drag_size.height() + delta.y())
            self._window.resize(new_w, new_h)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._drag_size = None


# =================================================================================================
#  Main Window
# =================================================================================================

class MainWindow(QMainWindow):
    def __init__(self, framework_root: str):
        super().__init__()
        self.framework_root = framework_root
        self.registry = TestRegistry(framework_root)
        self.runner = TestRunner(framework_root, parent=self)
        self._tree_item_map: dict[int, SteerTestInfo] = {}  # id(item) -> test_info
        self._batch_results: list[tuple[str, int, str]] = []
        self._updating_params = False  # prevent signal recursion
        self._dynamic_param_widgets: list[tuple[dict, QWidget]] = []  # (param_def, widget)
        self.settings = QSettings("STEER", "STEER-GUI")
        self._register_custom_tests()

        # Frameless window with translucent background for rounded corners
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(1100, 700)
        self._restore_geometry()

        self._setup_ui()
        self._connect_signals()
        self._update_status_bar()

    # ── Painting (rounded corners) ────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Drop shadow (subtle)
        shadow_color = QColor(0, 0, 0, 60)
        for i in range(4):
            p.setPen(Qt.PenStyle.NoPen)
            shadow_color.setAlpha(15 - i * 3)
            p.setBrush(shadow_color)
            offset = i + 1
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(offset, offset, self.width() - 2 * offset, self.height() - 2 * offset),
                CORNER_RADIUS + offset, CORNER_RADIUS + offset
            )
            p.drawPath(path)

        # Main background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLORS["bg_primary"]))
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(4, 4, self.width() - 8, self.height() - 8),
            CORNER_RADIUS, CORNER_RADIUS
        )
        p.drawPath(path)
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position resize grip at bottom-right
        if hasattr(self, '_resize_grip'):
            self._resize_grip.move(
                self.width() - self._resize_grip.width() - 6,
                self.height() - self._resize_grip.height() - 6,
            )

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Central widget container (with margins for the shadow area)
        outer = QWidget()
        outer.setObjectName("outerContainer")
        self.setCentralWidget(outer)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(0)
        outer.setStyleSheet("#outerContainer { background: transparent; }")

        # Title bar
        self.title_bar = TitleBar(self)
        outer_layout.addWidget(self.title_bar)

        # Content area
        content = QWidget()
        content.setObjectName("contentArea")
        content.setStyleSheet(f"#contentArea {{ background-color: {COLORS['bg_primary']}; }}")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(0)

        # Entropy source bar (compact, full width)
        entropy_row = QHBoxLayout()
        entropy_row.setSpacing(8)
        entropy_lbl = QLabel("Entropy:")
        entropy_lbl.setStyleSheet(f"color: {COLORS['accent_light']}; font-weight: bold; background: transparent;")
        entropy_row.addWidget(entropy_lbl)
        self.entropy_path = QLineEdit()
        self.entropy_path.setReadOnly(True)
        self.entropy_path.setPlaceholderText("Select an entropy file...")
        entropy_row.addWidget(self.entropy_path, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_entropy)
        entropy_row.addWidget(browse_btn)
        vd_label = QLabel("Validation:")
        vd_label.setStyleSheet(f"color: {COLORS['accent_light']}; font-weight: bold; background: transparent;")
        entropy_row.addWidget(vd_label)
        self.validation_combo = QComboBox()
        self.validation_combo.addItem("— Select —", "")
        for profile_id, path in self.registry.get_validation_data_files().items():
            self.validation_combo.addItem(f"{profile_id}.bin", path)
        self.validation_combo.currentIndexChanged.connect(self._on_validation_data_changed)
        entropy_row.addWidget(self.validation_combo)
        content_layout.addLayout(entropy_row)
        content_layout.addSpacing(6)

        # ── Main 3-column splitter ────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        content_layout.addWidget(splitter, 1)

        # ── Column 1: Available Tests ─────────────────────────────────────────
        col1 = QWidget()
        col1_layout = QVBoxLayout(col1)
        col1_layout.setContentsMargins(0, 0, 0, 0)
        col1_layout.setSpacing(4)

        col1_header = QLabel("Available Tests")
        col1_header.setObjectName("sectionHeader")
        col1_layout.addWidget(col1_header)

        self.test_tree = QTreeWidget()
        self.test_tree.setHeaderLabels(["Test", ""])
        self.test_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.test_tree.setRootIsDecorated(True)
        self.test_tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.test_tree.setColumnWidth(1, 30)
        self.test_tree.header().setStretchLastSection(False)
        self.test_tree.header().setSectionResizeMode(0, self.test_tree.header().ResizeMode.Stretch)
        self._populate_test_tree()
        col1_layout.addWidget(self.test_tree, 1)

        self.add_btn = QPushButton("Add to Plan >>")
        self.add_btn.clicked.connect(self._add_to_plan)
        col1_layout.addWidget(self.add_btn)

        self.add_custom_btn = QPushButton("+ Add Custom Test...")
        self.add_custom_btn.setToolTip(
            "Register a custom test binary that implements the STEER SDK interface"
        )
        self.add_custom_btn.clicked.connect(self._add_custom_test)
        col1_layout.addWidget(self.add_custom_btn)

        # ── Column 2: Plan + Parameters ───────────────────────────────────────
        col2 = QWidget()
        col2.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        col2_layout = QVBoxLayout(col2)
        col2_layout.setContentsMargins(6, 0, 6, 0)
        col2_layout.setSpacing(4)

        col2_header = QLabel("Planned Analysis")
        col2_header.setObjectName("sectionHeader")
        col2_layout.addWidget(col2_header)

        self.plan_list = QListWidget()
        self.plan_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.plan_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.plan_list.setWordWrap(True)
        self.plan_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.plan_list.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        col2_layout.addWidget(self.plan_list, 1)

        plan_btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("<< Remove")
        self.remove_btn.clicked.connect(self._remove_from_plan)
        self.clear_plan_btn = QPushButton("Clear All")
        self.clear_plan_btn.clicked.connect(self._clear_plan)
        plan_btn_row.addWidget(self.remove_btn)
        plan_btn_row.addWidget(self.clear_plan_btn)
        plan_btn_row.addStretch()
        col2_layout.addLayout(plan_btn_row)

        # Parameters (compact, within column 2)
        param_group = QGroupBox("Parameters")
        param_group.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        param_group.setMinimumWidth(0)
        param_group.setMaximumWidth(16777215)  # allow shrinking below size hint
        pg_layout = QVBoxLayout(param_group)
        pg_layout.setSpacing(2)
        pg_layout.setContentsMargins(0, 8, 0, 0)

        self.param_test_label = QLabel("Select a planned test")
        self.param_test_label.setObjectName("statusLabel")
        self.param_test_label.setWordWrap(True)
        pg_layout.addWidget(self.param_test_label)

        # Common editable parameters
        cg = QGridLayout()
        cg.setSpacing(2)
        cg.setColumnStretch(0, 0)
        cg.setColumnStretch(1, 1)
        cg.setColumnStretch(2, 0)
        cg.setColumnStretch(3, 1)
        lbl_s = QLabel("Streams:")
        lbl_s.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        cg.addWidget(lbl_s, 0, 0)
        self.bitstream_count = QSpinBox()
        self.bitstream_count.setRange(1, 10000)
        self.bitstream_count.setValue(1)
        self.bitstream_count.setMinimumWidth(0)
        self.bitstream_count.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        cg.addWidget(self.bitstream_count, 0, 1)
        lbl_l = QLabel("Len:")
        lbl_l.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        cg.addWidget(lbl_l, 0, 2)
        self.bitstream_length = QSpinBox()
        self.bitstream_length.setRange(1024, 100000000)
        self.bitstream_length.setSingleStep(100000)
        self.bitstream_length.setValue(1000000)
        self.bitstream_length.setMinimumWidth(0)
        self.bitstream_length.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        cg.addWidget(self.bitstream_length, 0, 3)
        lbl_a = QLabel("Alpha:")
        lbl_a.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        cg.addWidget(lbl_a, 1, 0)
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0001, 0.5)
        self.alpha_spin.setDecimals(4)
        self.alpha_spin.setSingleStep(0.01)
        self.alpha_spin.setValue(0.01)
        self.alpha_spin.setMinimumWidth(0)
        self.alpha_spin.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        cg.addWidget(self.alpha_spin, 1, 1)
        lbl_r = QLabel("Report:")
        lbl_r.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        cg.addWidget(lbl_r, 1, 2)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["full", "standard", "summary"])
        self.level_combo.setMinimumWidth(0)
        self.level_combo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        cg.addWidget(self.level_combo, 1, 3)
        pg_layout.addLayout(cg)

        # Dynamic test-specific parameter container
        self._dyn_param_container = QWidget()
        self._dyn_param_layout = QGridLayout(self._dyn_param_container)
        self._dyn_param_layout.setSpacing(3)
        self._dyn_param_layout.setContentsMargins(0, 4, 0, 0)
        self._dyn_param_container.setVisible(False)
        pg_layout.addWidget(self._dyn_param_container)

        # Causal model bit assignment button (hidden until a causal test is selected)
        self._bit_config_btn = QPushButton("Configure Bit Positions…")
        self._bit_config_btn.setToolTip(
            "Open the interactive bit-position assignment dialog\n"
            "for Treatment / Outcome / Covariate roles"
        )
        self._bit_config_btn.clicked.connect(self._open_bit_array_dialog)
        self._bit_config_btn.setVisible(False)
        pg_layout.addWidget(self._bit_config_btn)

        # Compact label showing current bit config
        self._bit_summary_label = QLabel()
        self._bit_summary_label.setWordWrap(True)
        self._bit_summary_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 8pt; padding: 0 2px;"
        )
        self._bit_summary_label.setVisible(False)
        pg_layout.addWidget(self._bit_summary_label)

        param_actions = QHBoxLayout()
        self.apply_to_all_btn = QPushButton("Apply to All")
        self.apply_to_all_btn.setToolTip("Apply current parameters to all planned tests")
        self.apply_to_all_btn.clicked.connect(self._apply_params_to_all)
        param_actions.addWidget(self.apply_to_all_btn)
        param_actions.addStretch()
        pg_layout.addLayout(param_actions)

        col2_layout.addWidget(param_group)

        # Run / Stop row
        run_row = QHBoxLayout()
        self.run_btn = QPushButton("RUN TESTS")
        self.run_btn.setObjectName("runButton")
        self.run_btn.clicked.connect(self._run_tests)
        run_row.addWidget(self.run_btn, 1)
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self._stop_tests)
        self.stop_btn.setVisible(False)
        run_row.addWidget(self.stop_btn, 1)
        col2_layout.addLayout(run_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        col2_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("statusLabel")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col2_layout.addWidget(self.progress_label)

        # ── Column 3: Results / Log / Docs ────────────────────────────────────
        col3 = QWidget()
        col3_layout = QVBoxLayout(col3)
        col3_layout.setContentsMargins(0, 0, 0, 0)

        self.right_tabs = QTabWidget()

        self.report_viewer = ReportViewer()
        self.right_tabs.addTab(self.report_viewer, "Results")

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.right_tabs.addTab(self.log_output, "Log")

        self.docs_viewer = DocsViewer()
        self.right_tabs.addTab(self.docs_viewer, "Documentation")

        col3_layout.addWidget(self.right_tabs)

        # Add columns to splitter with size policies
        col1.setMinimumWidth(180)
        col2.setMinimumWidth(170)
        col3.setMinimumWidth(250)
        splitter.addWidget(col1)
        splitter.addWidget(col2)
        splitter.addWidget(col3)
        splitter.setStretchFactor(0, 0)  # col1 doesn't stretch
        splitter.setStretchFactor(1, 0)  # col2 doesn't stretch
        splitter.setStretchFactor(2, 1)  # col3 gets extra space
        splitter.setSizes([280, 320, 600])

        outer_layout.addWidget(content, 1)

        # Status bar (bottom strip)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; padding: 4px 16px; "
            f"background: {COLORS['bg_secondary']}; "
            f"border-bottom-left-radius: {CORNER_RADIUS}px; "
            f"border-bottom-right-radius: {CORNER_RADIUS}px;"
        )
        outer_layout.addWidget(self.status_label)

        # Resize grip
        self._resize_grip = ResizeGrip(self)

    def update_inline_styles(self):
        """Refresh widgets that use inline COLORS references after a theme switch."""
        # Title bar elements
        tb = self.title_bar
        tb.title_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 9pt; "
            f"font-weight: 500; background: transparent;"
        )
        btn_style_base = (
            "QPushButton {{ background: transparent; border: none; "
            "border-radius: 8px; color: {color}; font-size: {size}; "
            "padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            "QPushButton:hover {{ background-color: {hover_bg}; }}"
        )
        tb.theme_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 8px; color: {COLORS['text_secondary']}; font-size: 13pt; "
            f"padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}"
        )
        tb.minimize_btn.setStyleSheet(btn_style_base.format(
            color=COLORS["text_secondary"], size="12pt",
            hover_bg=COLORS["bg_tertiary"]
        ))
        tb.maximize_btn.setStyleSheet(btn_style_base.format(
            color=COLORS["text_secondary"], size="11pt",
            hover_bg=COLORS["bg_tertiary"]
        ))
        tb.close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 8px; color: {COLORS['text_secondary']}; font-size: 10pt; "
            f"padding: 0px; min-width: 36px; min-height: 28px; max-width: 36px; max-height: 28px; }}"
            f"QPushButton:hover {{ background-color: {COLORS['failure']}; color: white; }}"
        )
        # Content area and status bar
        self.findChild(QWidget, "contentArea").setStyleSheet(
            f"#contentArea {{ background-color: {COLORS['bg_primary']}; }}"
        )
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; padding: 4px 16px; "
            f"background: {COLORS['bg_secondary']}; "
            f"border-bottom-left-radius: {CORNER_RADIUS}px; "
            f"border-bottom-right-radius: {CORNER_RADIUS}px;"
        )
        # Force repaint for rounded corner background
        self.update()

    # ── Test Tree Population ──────────────────────────────────────────────────

    def _populate_test_tree(self):
        self.test_tree.clear()
        self._tree_item_map.clear()

        testu01_redundant = {"Serial Over", "Linear Complexity", "Weight Distribution"}

        def _add_test_item(parent, test, lang, lang_color, redundant=False):
            display = test.display_name
            if redundant:
                display += " *"
            item = QTreeWidgetItem(parent, [display, lang])
            item.setForeground(1, QColor(lang_color))
            if not test.is_available:
                tip = "Executable not built yet"
                if redundant:
                    tip += " (similar test exists in NIST STS)"
                item.setToolTip(0, tip)
            elif redundant:
                item.setToolTip(0, "Similar test exists in NIST STS")
            self._tree_item_map[id(item)] = test

        nist_group = QTreeWidgetItem(self.test_tree, [
            f"NIST Statistical Tests ({len(self.registry.nist_tests())})", ""
        ])
        nist_group.setExpanded(True)
        for test in self.registry.nist_tests():
            _add_test_item(nist_group, test, "C", COLORS["text_muted"])

        dh_tests = self.registry.diehard_tests()
        if dh_tests:
            dh_group = QTreeWidgetItem(self.test_tree, [
                f"Diehard Tests ({len(dh_tests)})", ""
            ])
            dh_group.setExpanded(True)
            for test in dh_tests:
                _add_test_item(dh_group, test, "C", COLORS["text_muted"])

        tu01_tests = self.registry.testu01_tests()
        if tu01_tests:
            tu01_group = QTreeWidgetItem(self.test_tree, [
                f"TestU01 Tests ({len(tu01_tests)})", ""
            ])
            tu01_group.setExpanded(True)
            for test in tu01_tests:
                _add_test_item(tu01_group, test, "C", COLORS["text_muted"],
                               redundant=(test.display_name in testu01_redundant))

        ais_tests = self.registry.ais_tests()
        if ais_tests:
            ais_group = QTreeWidgetItem(self.test_tree, [
                f"AIS 20/31 Tests ({len(ais_tests)})", ""
            ])
            ais_group.setExpanded(True)
            for test in ais_tests:
                _add_test_item(ais_group, test, "Python", COLORS["accent_highlight"])

        py_tests = self.registry.python_tests()
        if py_tests:
            py_group = QTreeWidgetItem(self.test_tree, [
                f"Anametric Causal Tests ({len(py_tests)})", ""
            ])
            py_group.setExpanded(True)
            for test in py_tests:
                _add_test_item(py_group, test, "Python", COLORS["accent_highlight"])

        # Custom tests
        custom_tests = [t for t in self.registry.tests
                        if t.program_name.startswith("custom_")]
        if custom_tests:
            custom_group = QTreeWidgetItem(self.test_tree, [
                f"Custom Tests ({len(custom_tests)})", ""
            ])
            custom_group.setExpanded(True)
            for test in custom_tests:
                _add_test_item(custom_group, test, "Ext", COLORS["warning"])

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.runner.test_started.connect(self._on_test_started)
        self.runner.test_output.connect(self._on_test_output)
        self.runner.test_completed.connect(self._on_test_completed)
        self.runner.test_error.connect(self._on_test_error)
        self.runner.batch_progress.connect(self._on_batch_progress)
        self.runner.batch_completed.connect(self._on_batch_completed)
        self.test_tree.itemDoubleClicked.connect(self._on_test_double_clicked)
        self.test_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.test_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.plan_list.currentItemChanged.connect(self._on_plan_selection_changed)
        self.plan_list.itemClicked.connect(self._on_plan_item_clicked)
        self.bitstream_count.valueChanged.connect(self._on_param_changed)
        self.bitstream_length.valueChanged.connect(self._on_param_changed)
        self.alpha_spin.valueChanged.connect(self._on_param_changed)
        self.level_combo.currentIndexChanged.connect(self._on_param_changed)

    def _on_test_double_clicked(self, item, column):
        """Open documentation for the double-clicked test."""
        test_info = self._tree_item_map.get(id(item))
        if test_info:
            self.right_tabs.setCurrentWidget(self.docs_viewer)
            test_key = (test_info.program_name
                        .replace("nist_sts_", "").replace("diehard_", "")
                        .replace("testu01_", "").replace("_test", ""))
            self.docs_viewer.select_test(test_key)

    def _on_tree_context_menu(self, pos):
        """Show context menu for the test tree (remove custom tests)."""
        from PyQt6.QtWidgets import QMenu
        item = self.test_tree.itemAt(pos)
        if not item:
            return
        info = self._tree_item_map.get(id(item))
        if not info or not info.program_name.startswith("custom_"):
            return
        menu = QMenu(self)
        remove_action = menu.addAction(f"Remove \"{info.display_name}\"")
        action = menu.exec(self.test_tree.viewport().mapToGlobal(pos))
        if action == remove_action:
            self._remove_custom_test()

    # ── Plan Management ───────────────────────────────────────────────────────

    def _get_editable_params(self, program_name: str) -> list[dict]:
        """Look up test-specific editable parameters for a program."""
        best_match = ""
        best_params: list[dict] = []
        for prefix, params in TEST_EDITABLE_PARAMS.items():
            if program_name.startswith(prefix) and len(prefix) > len(best_match):
                best_match = prefix
                best_params = params
        return best_params

    def _format_plan_label(self, name: str, params: dict) -> str:
        """Format a plan item label with params in parentheses."""
        length = params["bitstream_length"]
        if length >= 1000000:
            length_str = f"{length // 1000000}M"
        elif length >= 1000:
            length_str = f"{length // 1000}K"
        else:
            length_str = str(length)
        parts = [f"{params['bitstream_count']}\u00d7{length_str}"]
        # Include test-specific params compactly
        test_params = params.get("test_params", {})
        for k, v in test_params.items():
            short_key = k.split()[-1] if " " in k else k
            if isinstance(v, float):
                parts.append(f"{short_key}={v:.2g}")
            else:
                parts.append(f"{short_key}={v}")
        # Include bit config summary for causal tests
        bc = params.get("bit_config")
        if bc:
            t = ",".join(str(p) for p in bc.get("treatpos", []))
            o = ",".join(str(p) for p in bc.get("outpos", []))
            parts.append(f"T=[{t}] O=[{o}]")
        return f"{name} ({', '.join(parts)})"

    def _rebuild_dynamic_params(self, program_name: str, test_params: dict):
        """Rebuild the dynamic parameter widgets for the selected test."""
        # Clear old dynamic widgets — delete immediately via sip if available
        for _, w in self._dynamic_param_widgets:
            w.setParent(None)
        self._dynamic_param_widgets.clear()
        # Remove old labels too
        while self._dyn_param_layout.count():
            child = self._dyn_param_layout.takeAt(0)
            w = child.widget()
            if w:
                w.setParent(None)

        param_defs = self._get_editable_params(program_name)
        if not param_defs:
            self._dyn_param_container.setVisible(False)
            return

        self._dyn_param_container.setVisible(True)
        self._dyn_param_layout.setColumnStretch(0, 0)
        self._dyn_param_layout.setColumnStretch(1, 1)
        self._dyn_param_layout.setColumnStretch(2, 0)
        self._dyn_param_layout.setColumnStretch(3, 1)
        row = 0
        col = 0
        for pdef in param_defs:
            lbl = QLabel(f"{pdef['label']}:")
            if pdef["type"] == "float":
                w = QDoubleSpinBox()
                w.setRange(pdef["min"], pdef["max"])
                w.setDecimals(3)
                w.setSingleStep(0.05)
                w.setValue(test_params.get(pdef["key"], pdef["default"]))
            else:
                w = QSpinBox()
                w.setRange(pdef["min"], pdef["max"])
                w.setValue(test_params.get(pdef["key"], pdef["default"]))
            w.valueChanged.connect(self._on_param_changed)
            w.setMinimumWidth(0)
            w.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self._dyn_param_layout.addWidget(lbl, row, col * 2)
            self._dyn_param_layout.addWidget(w, row, col * 2 + 1)
            self._dynamic_param_widgets.append((pdef, w))
            col += 1
            if col >= 2:
                col = 0
                row += 1
        # Force layout recalculation
        self._dyn_param_layout.activate()
        self._dyn_param_container.adjustSize()
        self._dyn_param_container.updateGeometry()

    def _add_to_plan(self):
        """Add selected tests from the tree to the planned analysis list."""
        selected_items = self.test_tree.selectedItems()
        added = 0
        for item in selected_items:
            test_info = self._tree_item_map.get(id(item))
            if test_info is None:
                continue

            # Build default test-specific params
            test_params = {}
            for pdef in self._get_editable_params(test_info.program_name):
                test_params[pdef["key"]] = pdef["default"]

            params = {
                "bitstream_count": self.bitstream_count.value(),
                "bitstream_length": self.bitstream_length.value(),
                "alpha": self.alpha_spin.value(),
                "report_level": self.level_combo.currentText(),
                "test_params": test_params,
            }

            # Add default bit config for causal tests
            if self._is_causal_test(test_info.program_name):
                params["bit_config"] = self._default_bit_config(test_info.program_name)

            plan_item = QListWidgetItem(
                self._format_plan_label(test_info.display_name, params)
            )
            plan_item.setData(TEST_INFO_ROLE, test_info.program_name)
            plan_item.setData(PLAN_DATA_ROLE, params)
            self.plan_list.addItem(plan_item)
            added += 1

        if added:
            self._update_status_bar()

    def _remove_from_plan(self):
        for item in reversed(self.plan_list.selectedItems()):
            self.plan_list.takeItem(self.plan_list.row(item))
        self._update_status_bar()

    def _clear_plan(self):
        self.plan_list.clear()
        self.param_test_label.setText("Select a planned test")
        self._rebuild_dynamic_params("", {})
        self._update_status_bar()

    def _on_plan_selection_changed(self, current, previous):
        if current is None:
            self.param_test_label.setText("Select a planned test")
            self._rebuild_dynamic_params("", {})
            self._bit_config_btn.setVisible(False)
            self._bit_summary_label.setVisible(False)
            return

        self._updating_params = True
        params = current.data(PLAN_DATA_ROLE) or {}
        program_name = current.data(TEST_INFO_ROLE) or ""

        label = current.text()
        display_name = label.split(" (")[0] if " (" in label else label
        self.param_test_label.setText(f"Editing: {display_name}")

        self.bitstream_count.setValue(params.get("bitstream_count", 1))
        self.bitstream_length.setValue(params.get("bitstream_length", 1000000))
        self.alpha_spin.setValue(params.get("alpha", 0.01))
        level = params.get("report_level", "full")
        idx = self.level_combo.findText(level)
        if idx >= 0:
            self.level_combo.setCurrentIndex(idx)

        self._rebuild_dynamic_params(program_name, params.get("test_params", {}))

        # Show/hide causal model bit config
        is_causal = self._is_causal_test(program_name)
        self._bit_config_btn.setVisible(is_causal)
        if is_causal:
            self._update_bit_summary(params)
            self._bit_summary_label.setVisible(True)
        else:
            self._bit_summary_label.setVisible(False)

        self._updating_params = False

    def _on_plan_item_clicked(self, item):
        """Refresh params on click even if item was already current."""
        if item is not None:
            self._on_plan_selection_changed(item, None)

    def _on_param_changed(self):
        if self._updating_params:
            return
        current = self.plan_list.currentItem()
        if current is None:
            return

        # Read test-specific params from dynamic widgets
        test_params = {}
        for pdef, w in self._dynamic_param_widgets:
            test_params[pdef["key"]] = w.value()

        params = {
            "bitstream_count": self.bitstream_count.value(),
            "bitstream_length": self.bitstream_length.value(),
            "alpha": self.alpha_spin.value(),
            "report_level": self.level_combo.currentText(),
            "test_params": test_params,
        }
        # Preserve bit config for causal tests
        old_params = current.data(PLAN_DATA_ROLE) or {}
        if "bit_config" in old_params:
            params["bit_config"] = old_params["bit_config"]
        current.setData(PLAN_DATA_ROLE, params)

        label = current.text()
        display_name = label.split(" (")[0] if " (" in label else label
        current.setText(self._format_plan_label(display_name, params))

    def _apply_params_to_all(self):
        """Apply current common parameter values to all tests in the plan."""
        for i in range(self.plan_list.count()):
            item = self.plan_list.item(i)
            params = item.data(PLAN_DATA_ROLE) or {}
            params["bitstream_count"] = self.bitstream_count.value()
            params["bitstream_length"] = self.bitstream_length.value()
            params["alpha"] = self.alpha_spin.value()
            params["report_level"] = self.level_combo.currentText()
            item.setData(PLAN_DATA_ROLE, params)
            label = item.text()
            display_name = label.split(" (")[0] if " (" in label else label
            item.setText(self._format_plan_label(display_name, params))

    # ── Causal Model Bit Config ─────────────────────────────────────────────

    @staticmethod
    def _is_causal_test(program_name: str) -> bool:
        return program_name in ("pearl_causal_model_test", "rubin_causal_model_test")

    @staticmethod
    def _causal_model_name(program_name: str) -> str:
        if "pearl" in program_name:
            return "pearl"
        return "rubin"

    def _default_bit_config(self, program_name: str) -> dict:
        cfg = {
            "block_size": 6,
            "treatpos": [0, 1],
            "outpos": [2, 3, 4, 5],
            "alphabet_size": 3,
        }
        if "pearl" in program_name:
            cfg["state_bits"] = 2
            cfg["null_simulations"] = 200
        return cfg

    def _update_bit_summary(self, params: dict):
        bc = params.get("bit_config")
        if not bc:
            self._bit_summary_label.setText("No bit positions configured yet")
            return
        treat = ", ".join(str(p) for p in bc.get("treatpos", []))
        out = ", ".join(str(p) for p in bc.get("outpos", []))
        k = bc.get("alphabet_size", 2)
        text = f"Block={bc.get('block_size', '?')}  T=[{treat}]  O=[{out}]  k={k}"
        if "state_bits" in bc:
            text += f"  state_bits={bc['state_bits']}"
        if "null_simulations" in bc:
            text += f"  sims={bc['null_simulations']}"
        self._bit_summary_label.setText(text)

    def _open_bit_array_dialog(self):
        current = self.plan_list.currentItem()
        if current is None:
            return
        program_name = current.data(TEST_INFO_ROLE) or ""
        if not self._is_causal_test(program_name):
            return

        params = current.data(PLAN_DATA_ROLE) or {}
        bc = params.get("bit_config") or self._default_bit_config(program_name)
        model = self._causal_model_name(program_name)

        extra = {"alphabet_size": bc.get("alphabet_size", 3)}
        if model == "pearl":
            extra["state_bits"] = bc.get("state_bits", 2)
            extra["null_simulations"] = bc.get("null_simulations", 200)

        dlg = BitArrayDialog(
            model_name=model,
            block_size=bc.get("block_size", 6),
            treatpos=bc.get("treatpos", [0, 1]),
            outpos=bc.get("outpos", [2, 3, 4, 5]),
            extra=extra,
            parent=self,
        )
        if dlg.exec() == dlg.DialogCode.Accepted:
            result = dlg.get_result()
            params["bit_config"] = result
            current.setData(PLAN_DATA_ROLE, params)
            self._update_bit_summary(params)
            # Update plan label
            label = current.text()
            display_name = label.split(" (")[0] if " (" in label else label
            current.setText(self._format_plan_label(display_name, params))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_entropy(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Entropy File",
            str(Path(self.framework_root) / "data"),
            "Binary Files (*.bin);;All Files (*)"
        )
        if path:
            self.entropy_path.setText(path)
            self.validation_combo.setCurrentIndex(0)

    def _on_validation_data_changed(self, index):
        path = self.validation_combo.currentData()
        if path:
            self.entropy_path.setText(path)

    def _build_parameters(self, test_info: SteerTestInfo, params: dict) -> dict:
        param_list = [
            {
                "name": "bitstream count",
                "data type": "unsigned 64-bit integer",
                "units": "bitstreams",
                "value": str(params["bitstream_count"]),
            },
            {
                "name": "bitstream length",
                "data type": "unsigned 64-bit integer",
                "units": "bits",
                "value": str(params["bitstream_length"]),
            },
            {
                "name": "significance level (alpha)",
                "data type": "double precision floating point",
                "precision": "6",
                "value": str(params["alpha"]),
            },
        ]
        # Add test-specific parameters
        test_params = params.get("test_params", {})
        for key, value in test_params.items():
            if isinstance(value, float):
                param_list.append({
                    "name": key,
                    "data type": "double precision floating point",
                    "precision": "6",
                    "value": str(value),
                })
            else:
                param_list.append({
                    "name": key,
                    "data type": "unsigned 64-bit integer",
                    "value": str(value),
                })
        # Add causal model bit config parameters
        bc = params.get("bit_config")
        if bc:
            param_list.append({
                "name": "subsequence size",
                "data type": "signed 32-bit integer",
                "value": str(bc.get("block_size", 6)),
            })
            param_list.append({
                "name": "treatment positions",
                "data type": "utf-8 string",
                "value": ",".join(str(p) for p in bc.get("treatpos", [0, 1])),
            })
            param_list.append({
                "name": "outcome positions",
                "data type": "utf-8 string",
                "value": ",".join(str(p) for p in bc.get("outpos", [2, 3, 4, 5])),
            })
            param_list.append({
                "name": "alphabet size",
                "data type": "signed 32-bit integer",
                "value": str(bc.get("alphabet_size", 3)),
            })
            if "state_bits" in bc:
                param_list.append({
                    "name": "state bits",
                    "data type": "signed 32-bit integer",
                    "value": str(bc.get("state_bits", 2)),
                })
            if "null_simulations" in bc:
                param_list.append({
                    "name": "null simulations",
                    "data type": "signed 32-bit integer",
                    "value": str(bc.get("null_simulations", 200)),
                })

        return {
            "parameter set": {
                "test name": test_info.display_name.lower(),
                "parameter set name": "gui",
                "parameters": param_list,
            }
        }

    def _run_tests(self):
        entropy_file = self.entropy_path.text()
        if not entropy_file:
            QMessageBox.warning(self, "Missing Input", "Please select an entropy source file.")
            return

        count = self.plan_list.count()
        if count == 0:
            QMessageBox.warning(self, "No Tests",
                                "Add tests to the Planned Analysis list before running.")
            return

        self._batch_results.clear()
        self.log_output.clear()
        self._log("Starting test run...")
        self._log(f"Entropy source: {entropy_file}")
        self._log(f"Planned tests: {count}")
        self._log("")

        # Build test registry lookup
        test_lookup = {t.program_name: t for t in self.registry.tests}

        configs = []
        skipped = []
        for i in range(count):
            item = self.plan_list.item(i)
            program_name = item.data(TEST_INFO_ROLE)
            params = item.data(PLAN_DATA_ROLE)
            test_info = test_lookup.get(program_name)
            if not test_info:
                continue
            if not test_info.is_available:
                skipped.append(test_info.display_name)
                continue

            configs.append({
                "test_name": test_info.display_name,
                "program_name": test_info.program_name,
                "executable_path": test_info.executable_path,
                "test_type": test_info.test_type,
                "entropy_file": entropy_file,
                "parameters": self._build_parameters(test_info, params),
                "report_level": params.get("report_level", "full"),
            })

        if skipped:
            self._log(f"Note: {len(skipped)} test(s) skipped (not built): "
                      f"{', '.join(skipped)}")
            self._log("")

        if not configs:
            QMessageBox.warning(self, "No Runnable Tests",
                                "None of the planned tests have built executables.")
            return

        self.run_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(configs))
        self.progress_bar.setValue(0)
        self.right_tabs.setCurrentIndex(1)

        self.runner.run_tests(configs)

    def _stop_tests(self):
        self.runner.stop()
        self._log("\n[STOPPED] Test run cancelled by user.")
        self._restore_run_state()

    def _open_report(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Report",
            str(Path(self.framework_root) / "results"),
            "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self.report_viewer.load_report(path)
            self.right_tabs.setCurrentIndex(0)

    # ── Runner Signals ────────────────────────────────────────────────────────

    def _on_test_started(self, test_name):
        self._log(f"  Running: {test_name}")
        self.status_label.setText(f"Running: {test_name}")

    def _on_test_output(self, test_name, text):
        for line in text.strip().splitlines():
            self._log(f"    {line}")

    def _on_test_completed(self, test_name, exit_code, report_path):
        try:
            report_data = json.loads(Path(report_path).read_text())
            report = report_data.get("report", report_data)
            evaluation = _nuanced_eval(report)
            badge_text, _ = _eval_badge(evaluation)
            self._log(f"  {test_name}: {badge_text}")
        except Exception:
            status = "PASS" if exit_code == 0 else f"FAIL (exit code {exit_code})"
            self._log(f"  {test_name}: {status}")

        self._log("")
        self._batch_results.append((test_name, exit_code, report_path))

    def _on_test_error(self, test_name, error):
        self._log(f"  ERROR: {test_name}: {error}")
        self._batch_results.append((test_name, -1, ""))

    def _on_batch_progress(self, completed, total):
        self.progress_bar.setValue(completed)
        self.progress_label.setText(f"{completed} of {total} tests complete")

    def _on_batch_completed(self, total, passed, failed):
        self._log(f"{'=' * 50}")
        self._log(f"Batch complete: {passed} passed, {failed} failed, {total} total")
        self._restore_run_state()
        self.progress_bar.setValue(total)
        self.progress_label.setText(f"Done: {passed} passed, {failed} failed")

        if len(self._batch_results) == 1 and self._batch_results[0][2]:
            self.report_viewer.load_report(self._batch_results[0][2])
        elif self._batch_results:
            self.report_viewer.load_batch_results(self._batch_results)
        self.right_tabs.setCurrentIndex(0)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, text: str):
        self.log_output.appendPlainText(text)

    def _restore_run_state(self):
        self.run_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.status_label.setText("Ready")

    def _update_status_bar(self):
        total = len(self.registry.tests)
        available = len(self.registry.available_tests())
        planned = self.plan_list.count()
        self.status_label.setText(
            f"Ready  ·  {available}/{total} tests available  ·  "
            f"{planned} test(s) planned  ·  {self.framework_root}"
        )

    def _restore_geometry(self):
        geom = self.settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        # Restore saved theme
        saved_theme = self.settings.value("theme", "dark")
        if saved_theme != current_mode() and saved_theme in THEME_IDS:
            set_mode(saved_theme)
            from theme import STYLESHEET
            QApplication.instance().setStyleSheet(STYLESHEET)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("theme", current_mode())
        if self.runner.is_running():
            self.runner.stop()
        super().closeEvent(event)

    # ── Custom Test Management ────────────────────────────────────────────────

    def _load_custom_tests(self) -> list[dict]:
        """Load custom test definitions from QSettings."""
        data = self.settings.value("custom_tests", [])
        if not isinstance(data, list):
            return []
        return data

    def _save_custom_tests(self, tests: list[dict]):
        """Persist custom test definitions to QSettings."""
        self.settings.setValue("custom_tests", tests)

    def _register_custom_tests(self):
        """Register saved custom tests into the registry and tree."""
        for entry in self._load_custom_tests():
            self._register_one_custom(entry)

    def _register_one_custom(self, entry: dict):
        """Add a single custom test to the registry (doesn't touch settings)."""
        name = entry.get("name", "Custom Test")
        exe = entry.get("executable", "")
        test_type = entry.get("test_type", "nist-sts")
        program_name = f"custom_{name.lower().replace(' ', '_')}"
        # Avoid duplicates
        if any(t.program_name == program_name for t in self.registry.tests):
            return
        info = SteerTestInfo(
            display_name=name,
            program_name=program_name,
            test_type=test_type,
            executable_path=exe,
            is_available=bool(exe and Path(exe).exists()),
        )
        self.registry.tests.append(info)

    def _add_custom_test(self):
        """Show dialog to register a custom test binary."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dlg = QDialog(self)
        dlg.setWindowTitle("Add Custom Test")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout(dlg)

        # Name
        layout.addWidget(QLabel("Test display name:"))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. My Custom Test")
        layout.addWidget(name_edit)

        # Executable path
        layout.addWidget(QLabel("Path to executable / script:"))
        exe_row = QHBoxLayout()
        exe_edit = QLineEdit()
        exe_edit.setPlaceholderText("Select binary implementing the STEER SDK interface...")
        exe_row.addWidget(exe_edit, 1)
        browse_btn = QPushButton("Browse")
        def _browse():
            path, _ = QFileDialog.getOpenFileName(
                dlg, "Select Test Executable", "",
                "Executables (*.exe *.sh *.py);;All Files (*)"
            )
            if path:
                exe_edit.setText(path)
        browse_btn.clicked.connect(_browse)
        exe_row.addWidget(browse_btn)
        layout.addLayout(exe_row)

        # Test type
        layout.addWidget(QLabel("Test type:"))
        type_combo = QComboBox()
        type_combo.addItems(["nist-sts", "diehard", "testu01", "python"])
        layout.addWidget(type_combo)

        # Help text
        help_lbl = QLabel(
            "The binary must accept STEER CLI arguments:\n"
            "  -l <level> -e <entropy> -p <params.json> -r <report.json> -R\n"
            "See the STEER Developer Guide for the full SDK interface."
        )
        help_lbl.setObjectName("statusLabel")
        help_lbl.setWordWrap(True)
        layout.addWidget(help_lbl)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name = name_edit.text().strip()
        exe_path = exe_edit.text().strip()
        if not name or not exe_path:
            QMessageBox.warning(self, "Missing Info",
                                "Please provide both a name and executable path.")
            return

        entry = {
            "name": name,
            "executable": exe_path,
            "test_type": type_combo.currentText(),
        }

        custom_tests = self._load_custom_tests()
        custom_tests.append(entry)
        self._save_custom_tests(custom_tests)
        self._register_one_custom(entry)
        self._populate_test_tree()
        self._update_status_bar()

    def _remove_custom_test(self):
        """Remove selected custom test(s) from the tree."""
        selected = self.test_tree.selectedItems()
        custom_tests = self._load_custom_tests()
        removed = False
        for item in selected:
            info = self._tree_item_map.get(id(item))
            if info and info.program_name.startswith("custom_"):
                display = info.display_name
                custom_tests = [
                    e for e in custom_tests if e.get("name") != display
                ]
                self.registry.tests = [
                    t for t in self.registry.tests
                    if t.program_name != info.program_name
                ]
                removed = True
        if removed:
            self._save_custom_tests(custom_tests)
            self._populate_test_tree()
            self._update_status_bar()
