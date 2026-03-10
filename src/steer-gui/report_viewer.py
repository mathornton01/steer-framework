# =================================================================================================
# report_viewer.py — Parse and display STEER JSON test reports
# =================================================================================================

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QApplication,
)

from theme import COLORS


class JsonHighlighter(QSyntaxHighlighter):
    """Simple JSON syntax highlighter."""

    def highlightBlock(self, text):
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor(COLORS["accent_light"]))
        key_fmt.setFontWeight(QFont.Weight.Bold)

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#98c379"))

        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor(COLORS["accent_highlight"]))

        bool_fmt = QTextCharFormat()
        bool_fmt.setForeground(QColor(COLORS["warning"]))

        import re
        # Keys
        for m in re.finditer(r'"([^"]*)"(?=\s*:)', text):
            self.setFormat(m.start(), m.end() - m.start(), key_fmt)
        # String values
        for m in re.finditer(r':\s*"([^"]*)"', text):
            start = text.index('"', m.start() + 1)
            self.setFormat(start, m.end() - start, str_fmt)
        # Numbers
        for m in re.finditer(r':\s*(-?\d+\.?\d*)', text):
            self.setFormat(m.start(1), m.end(1) - m.start(1), num_fmt)
        # Booleans
        for m in re.finditer(r'\b(true|false|null)\b', text):
            self.setFormat(m.start(), m.end() - m.start(), bool_fmt)


def _eval_badge(evaluation: str) -> tuple[str, str]:
    """Return (display_text, color) for an evaluation string."""
    e = evaluation.lower()
    if e == "pass":
        return "PASS", COLORS["success"]
    elif e == "fail":
        return "FAIL", COLORS["failure"]
    return "INCONCLUSIVE", COLORS["warning"]


class ReportViewer(QWidget):
    """Tabbed widget for viewing STEER test reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._report_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Summary tab
        self.summary_widget = QWidget()
        self.summary_layout = QVBoxLayout(self.summary_widget)
        self.summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tabs.addTab(self.summary_widget, "Summary")

        # Details tab
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["Field", "Value", "Status"])
        self.details_tree.setColumnWidth(0, 280)
        self.details_tree.setColumnWidth(1, 300)
        self.details_tree.setAlternatingRowColors(True)
        self.tabs.addTab(self.details_tree, "Details")

        # JSON tab
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        self.json_view = QPlainTextEdit()
        self.json_view.setReadOnly(True)
        self.json_highlighter = JsonHighlighter(self.json_view.document())
        json_layout.addWidget(self.json_view)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_json)
        btn_row.addStretch()
        btn_row.addWidget(copy_btn)
        json_layout.addLayout(btn_row)

        self.tabs.addTab(json_widget, "JSON")

        # Placeholder
        self._show_placeholder()

    def _show_placeholder(self):
        self._clear_summary()
        lbl = QLabel("Run a test to see results here.")
        lbl.setObjectName("statusLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_layout.addWidget(lbl)

    def _clear_summary(self):
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_report(self, report_path: str):
        """Load and display a STEER JSON report file."""
        try:
            data = json.loads(Path(report_path).read_text())
            self._report_data = data
            report = data.get("report", data)
            self._build_summary(report)
            self._build_details(report)
            self.json_view.setPlainText(json.dumps(data, indent=4))
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            self._clear_summary()
            lbl = QLabel(f"Error loading report: {e}")
            lbl.setStyleSheet(f"color: {COLORS['failure']};")
            lbl.setWordWrap(True)
            self.summary_layout.addWidget(lbl)

    def load_batch_results(self, results: list[tuple[str, int, str]]):
        """Display a batch summary from multiple test runs."""
        self._clear_summary()
        total = len(results)
        passed = sum(1 for _, code, _ in results if code == 0)
        failed = total - passed

        # Batch badge
        if failed == 0:
            badge_text, badge_color = "ALL PASSED", COLORS["success"]
        else:
            badge_text, badge_color = f"{failed} FAILED", COLORS["failure"]

        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            font-size: 18pt; font-weight: bold; color: {badge_color};
            padding: 16px; background-color: {COLORS['bg_tertiary']};
            border-radius: 8px; border: 2px solid {badge_color};
        """)
        self.summary_layout.addWidget(badge)

        stats = QLabel(f"{passed} passed  ·  {failed} failed  ·  {total} total")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setObjectName("statusLabel")
        self.summary_layout.addWidget(stats)

        # Per-test results
        for test_name, exit_code, report_path in results:
            row = QHBoxLayout()
            status_color = COLORS["success"] if exit_code == 0 else COLORS["failure"]
            status_text = "PASS" if exit_code == 0 else "FAIL"

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {status_color}; font-size: 14pt;")
            dot.setFixedWidth(24)
            row.addWidget(dot)

            name_lbl = QLabel(test_name)
            name_lbl.setStyleSheet("font-weight: bold;")
            row.addWidget(name_lbl, 1)

            status_lbl = QLabel(status_text)
            status_lbl.setStyleSheet(
                f"color: {status_color}; font-weight: bold; padding: 2px 8px;"
            )
            row.addWidget(status_lbl)

            container = QWidget()
            container.setLayout(row)
            self.summary_layout.addWidget(container)

        self.summary_layout.addStretch()

    def _build_summary(self, report: dict):
        self._clear_summary()

        # Evaluation badge
        evaluation = report.get("evaluation", "inconclusive")
        badge_text, badge_color = _eval_badge(evaluation)
        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            font-size: 20pt; font-weight: bold; color: {badge_color};
            padding: 20px; background-color: {COLORS['bg_tertiary']};
            border-radius: 8px; border: 2px solid {badge_color};
        """)
        self.summary_layout.addWidget(badge)

        # Metadata
        fields = [
            ("Test Name", report.get("test name", "")),
            ("Program", f"{report.get('program name', '')} v{report.get('program version', '')}"),
            ("Entropy Source", report.get("entropy source", "")),
            ("Duration", report.get("test duration", "")),
            ("Platform", f"{report.get('operating system', '')} / {report.get('architecture', '')}"),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold; min-width: 120px;")
            lbl.setFixedWidth(130)
            row.addWidget(lbl)
            val = QLabel(str(value))
            val.setWordWrap(True)
            row.addWidget(val, 1)
            container = QWidget()
            container.setLayout(row)
            self.summary_layout.addWidget(container)

        # Configuration summaries
        for config in report.get("configurations", []):
            config_eval = config.get("evaluation", "inconclusive")
            _, c_color = _eval_badge(config_eval)
            for test in config.get("tests", []):
                for calc in test.get("calculations", []):
                    if "probability" in calc.get("name", "").lower():
                        p_row = QHBoxLayout()
                        p_lbl = QLabel(f"  {calc['name']}:")
                        p_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
                        p_lbl.setFixedWidth(200)
                        p_row.addWidget(p_lbl)
                        p_val = QLabel(calc.get("value", ""))
                        p_val.setStyleSheet(f"color: {c_color}; font-weight: bold;")
                        p_row.addWidget(p_val, 1)
                        container = QWidget()
                        container.setLayout(p_row)
                        self.summary_layout.addWidget(container)

        self.summary_layout.addStretch()

    def _build_details(self, report: dict):
        self.details_tree.clear()

        # Configurations
        for config in report.get("configurations", []):
            config_eval = config.get("evaluation", "inconclusive")
            badge_text, _ = _eval_badge(config_eval)
            config_item = QTreeWidgetItem([
                f"Configuration {config.get('configuration id', '?')}",
                "", badge_text
            ])
            self._color_status(config_item, config_eval)
            self.details_tree.addTopLevelItem(config_item)

            for test in config.get("tests", []):
                test_eval = test.get("evaluation", "inconclusive")
                t_badge, _ = _eval_badge(test_eval)
                test_item = QTreeWidgetItem([
                    f"Test {test.get('test id', '?')}", "", t_badge
                ])
                self._color_status(test_item, test_eval)
                config_item.addChild(test_item)

                # Calculations
                for calc in test.get("calculations", []):
                    calc_item = QTreeWidgetItem([
                        calc.get("name", ""), calc.get("value", ""), ""
                    ])
                    test_item.addChild(calc_item)

                # Criteria
                for crit in test.get("criteria", []):
                    result = crit.get("result", False)
                    crit_item = QTreeWidgetItem([
                        crit.get("criterion", ""), "",
                        "PASS" if result else "FAIL"
                    ])
                    self._color_status(crit_item, "pass" if result else "fail")
                    test_item.addChild(crit_item)

            config_item.setExpanded(True)

        self.details_tree.expandAll()

    def _color_status(self, item: QTreeWidgetItem, evaluation: str):
        _, color = _eval_badge(evaluation)
        item.setForeground(2, QColor(color))

    def _copy_json(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.json_view.toPlainText())
