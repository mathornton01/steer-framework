# =================================================================================================
# docs_viewer.py — In-app documentation browser for STEER tests
# =================================================================================================

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QScrollArea,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from theme import COLORS


def _load_docs() -> dict:
    """Load test documentation JSON."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "docs" / "tests" / "test_documentation.json",
        Path(__file__).resolve().parent / "test_documentation.json",
    ]
    for c in candidates:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8"))
    return {}


class DocsViewer(QWidget):
    """Documentation browser widget for STEER tests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._docs = _load_docs()
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left: test list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Tests")
        header.setStyleSheet(
            f"font-weight: bold; font-size: 11pt; color: {COLORS['text_primary']}; "
            f"padding: 8px 12px; background-color: {COLORS['bg_secondary']}; "
            f"border-bottom: 1px solid {COLORS['border']};"
        )
        left_layout.addWidget(header)

        self.test_list = QListWidget()
        self.test_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        self.test_list.currentRowChanged.connect(self._on_test_selected)
        left_layout.addWidget(self.test_list)

        # Right: documentation content
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_primary']};
                border: none;
                padding: 16px;
                color: {COLORS['text_primary']};
                font-size: 10pt;
            }}
        """)

        splitter.addWidget(left)
        splitter.addWidget(self.content_area)
        splitter.setSizes([220, 580])

        self._populate_list()
        self._show_overview()

    def _populate_list(self):
        tests = self._docs.get("tests", {})

        # Group by category
        categories: dict[str, list] = {}
        for key, test in tests.items():
            cat = test.get("category", "Other")
            categories.setdefault(cat, []).append((key, test))

        for cat, items in categories.items():
            # Category header
            cat_item = QListWidgetItem(cat)
            cat_item.setFlags(Qt.ItemFlag.NoItemFlags)
            cat_font = QFont()
            cat_font.setBold(True)
            cat_font.setPointSize(9)
            cat_item.setFont(cat_font)
            cat_item.setForeground(QColor(COLORS["accent_light"]))
            cat_item.setData(Qt.ItemDataRole.UserRole, None)
            self.test_list.addItem(cat_item)

            for key, test in items:
                item = QListWidgetItem(f"  {test['name']}")
                item.setData(Qt.ItemDataRole.UserRole, key)
                self.test_list.addItem(item)

    def _on_test_selected(self, row):
        if row < 0:
            return
        item = self.test_list.item(row)
        key = item.data(Qt.ItemDataRole.UserRole)
        if key is None:
            return
        self._show_test(key)

    def _show_overview(self):
        tests = self._docs.get("tests", {})
        nist_count = sum(1 for t in tests.values() if t["category"] == "NIST Statistical Test Suite")
        causal_count = sum(1 for t in tests.values() if t["category"] == "Causal Model Tests")

        html = f"""
        <h2 style="color: {COLORS['accent_light']};">STEER Framework Test Documentation</h2>
        <p style="color: {COLORS['text_secondary']};">
            Select a test from the list to view its full documentation.
        </p>
        <hr style="border-color: {COLORS['border']};">
        <p><b style="color: {COLORS['accent_highlight']};">{nist_count}</b> NIST Statistical Test Suite tests (SP 800-22)</p>
        <p><b style="color: {COLORS['accent_highlight']};">{causal_count}</b> Causal Model tests</p>
        <p><b style="color: {COLORS['accent_highlight']};">{len(tests)}</b> total tests available</p>
        <hr style="border-color: {COLORS['border']};">
        <p style="color: {COLORS['text_muted']}; font-style: italic;">
            Documentation is also available via the command line:<br>
            <code style="color: {COLORS['accent_light']};">python steer_docs.py --list</code>
        </p>
        """
        self.content_area.setHtml(html)

    def _show_test(self, test_key: str):
        tests = self._docs.get("tests", {})
        test = tests.get(test_key)
        if not test:
            return

        accent = COLORS["accent_light"]
        orange = COLORS["accent_highlight"]
        secondary = COLORS["text_secondary"]
        muted = COLORS["text_muted"]
        success = COLORS["success"]
        failure = COLORS["failure"]
        bg_tert = COLORS["bg_tertiary"]
        border = COLORS["border"]

        # Build HTML
        html = f"""
        <h2 style="color: {accent}; margin-bottom: 4px;">{test['name']}</h2>
        <p style="color: {muted}; font-size: 9pt; margin-top: 0;">
            {test['category']} &nbsp;|&nbsp; {test['nist_reference']}
        </p>

        <div style="background-color: {bg_tert}; padding: 12px; border-radius: 6px;
                    border-left: 3px solid {orange}; margin: 12px 0;">
            <p style="color: {secondary}; margin: 0;">{test['summary']}</p>
        </div>

        <h3 style="color: {accent};">Description</h3>
        <p>{test['description'].replace(chr(10), '<br>')}</p>
        """

        if test.get("mathematical_basis"):
            html += f"""
            <h3 style="color: {accent};">Mathematical Basis</h3>
            <div style="background-color: {bg_tert}; padding: 10px; border-radius: 4px;
                        font-family: 'Consolas', monospace; font-size: 9pt;">
                {test['mathematical_basis'].replace(chr(10), '<br>')}
            </div>
            """

        if test.get("parameters"):
            html += f'<h3 style="color: {accent};">Parameters</h3><table cellpadding="6">'
            for pname, pdesc in test["parameters"].items():
                html += f"""
                <tr>
                    <td style="color: {orange}; font-weight: bold; vertical-align: top;
                              white-space: nowrap; font-family: monospace;">{pname}</td>
                    <td style="color: {secondary};">{pdesc}</td>
                </tr>
                """
            html += "</table>"

        if test.get("interpretation"):
            interp = test["interpretation"]
            html += f"""
            <h3 style="color: {accent};">Interpretation</h3>
            <table cellpadding="6">
                <tr>
                    <td style="color: {success}; font-weight: bold; width: 60px;">PASS</td>
                    <td>{interp.get('pass', '')}</td>
                </tr>
                <tr>
                    <td style="color: {failure}; font-weight: bold;">FAIL</td>
                    <td>{interp.get('fail', '')}</td>
                </tr>
            </table>
            """

        if test.get("recommendations"):
            html += f"""
            <h3 style="color: {accent};">Recommendations</h3>
            <p>{test['recommendations']}</p>
            """

        if test.get("example_applications"):
            html += f'<h3 style="color: {accent};">Example Applications</h3><ul>'
            for app in test["example_applications"]:
                html += f"<li>{app}</li>"
            html += "</ul>"

        html += f"""
        <hr style="border-color: {border};">
        <p style="color: {muted}; font-size: 8pt;">
            Program: <code>{test['program_name']}</code>
        </p>
        """

        self.content_area.setHtml(html)

    def select_test(self, test_key: str):
        """Select and display a test by its key (or partial match)."""
        for i in range(self.test_list.count()):
            item = self.test_list.item(i)
            item_key = item.data(Qt.ItemDataRole.UserRole)
            if item_key is None:
                continue
            # Try exact match first, then partial/normalized match
            if item_key == test_key or test_key in item_key or item_key in test_key:
                self.test_list.setCurrentRow(i)
                return
        # Fallback: try matching with underscores replaced by spaces
        normalized = test_key.replace("_", " ").lower()
        for i in range(self.test_list.count()):
            item = self.test_list.item(i)
            item_key = item.data(Qt.ItemDataRole.UserRole)
            if item_key is None:
                continue
            if normalized in item_key.lower() or item_key.lower() in normalized:
                self.test_list.setCurrentRow(i)
                return
