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
    elif e == "pass_warn":
        return "PASS*", COLORS["warning"]
    elif e == "fail":
        return "FAIL", COLORS["failure"]
    return "INCONCLUSIVE", COLORS["warning"]


# Criteria text patterns that indicate sample-size / statistical-power issues
# rather than actual test failures
_SAMPLE_SIZE_PATTERNS = [
    "bitstreams to test",           # "N bitstream tested >= minimum number of M bitstreams to test"
    "probability uniformity",       # "probability uniformity of 0.000 > 0.000" (can't assess with few samples)
    "uniformity assessment",        # "as required for probability uniformity assessment"
]


def _is_sample_size_criterion(criterion_text: str) -> bool:
    """Return True if a failing criterion is about insufficient sample size."""
    text = criterion_text.lower()
    return any(pat in text for pat in _SAMPLE_SIZE_PATTERNS)


def _nuanced_eval(report: dict) -> str:
    """Derive a nuanced evaluation from the report hierarchy.

    Returns:
        "pass"      – all configs and tests pass
        "pass_warn" – all statistical tests pass, but config-level criteria
                      fail only due to sample-size / statistical-power issues
        "fail"      – one or more statistical tests actually failed
        "inconclusive" – no configurations or missing data
    """
    configs = report.get("configurations", [])
    if not configs:
        return report.get("evaluation", "inconclusive").lower()

    overall = report.get("evaluation", "").lower()
    if overall == "pass":
        return "pass"

    all_tests_pass = True
    only_sample_size_failures = True

    for config in configs:
        # Check test-level evaluations
        for test in config.get("tests", []):
            if test.get("evaluation", "").lower() != "pass":
                all_tests_pass = False
                break
        if not all_tests_pass:
            break

        # Check config-level criteria — are failures only sample-size related?
        if config.get("evaluation", "").lower() == "fail":
            for crit in config.get("criteria", []):
                if not crit.get("result", False):
                    if not _is_sample_size_criterion(crit.get("criterion", "")):
                        only_sample_size_failures = False
                        break
        if not only_sample_size_failures:
            break

    if all_tests_pass and only_sample_size_failures:
        return "pass_warn"
    elif not all_tests_pass:
        return "fail"
    return overall


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
        self.details_tree.setColumnWidth(0, 220)
        self.details_tree.setColumnWidth(1, 240)
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

        # Read actual evaluation from each report JSON (not exit code)
        all_reports = []
        evaluations = []  # (test_name, evaluation_str)
        for test_name, exit_code, report_path in results:
            evaluation = None
            if report_path:
                try:
                    data = json.loads(Path(report_path).read_text())
                    all_reports.append((test_name, data))
                    report = data.get("report", data)
                    evaluation = _nuanced_eval(report)
                except Exception:
                    pass
            # Fallback: if no report or no evaluation field, use exit code
            if not evaluation:
                evaluation = "pass" if exit_code == 0 else "fail"
            evaluations.append((test_name, evaluation))

        passed = sum(1 for _, e in evaluations if e in ("pass", "pass_warn"))
        warned = sum(1 for _, e in evaluations if e == "pass_warn")
        failed = total - passed

        # Batch badge
        if failed == 0 and warned == 0:
            badge_text, badge_color = "ALL PASSED", COLORS["success"]
        elif failed == 0 and warned > 0:
            badge_text, badge_color = "ALL PASSED*", COLORS["warning"]
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

        # Warning explanation under badge
        if warned > 0:
            warn_note = QLabel(
                "⚠ PASS* = statistical tests passed but sample size is below "
                "the recommended minimum. Increase bitstream count for a "
                "definitive result."
            )
            warn_note.setWordWrap(True)
            warn_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn_note.setStyleSheet(
                f"color: {COLORS['warning']}; padding: 4px 12px; font-style: italic;"
            )
            self.summary_layout.addWidget(warn_note)

        warn_part = f"  ·  {warned} low-sample" if warned else ""
        stats = QLabel(f"{passed} passed{warn_part}  ·  {failed} failed  ·  {total} total")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setObjectName("statusLabel")
        self.summary_layout.addWidget(stats)

        # Per-test results
        for test_name, evaluation in evaluations:
            row = QHBoxLayout()
            badge_text, status_color = _eval_badge(evaluation)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {status_color}; font-size: 14pt;")
            dot.setFixedWidth(24)
            row.addWidget(dot)

            name_lbl = QLabel(test_name)
            name_lbl.setStyleSheet("font-weight: bold;")
            row.addWidget(name_lbl, 1)

            status_lbl = QLabel(badge_text)
            status_lbl.setStyleSheet(
                f"color: {status_color}; font-weight: bold; padding: 2px 8px;"
            )
            row.addWidget(status_lbl)

            container = QWidget()
            container.setLayout(row)
            self.summary_layout.addWidget(container)

            if evaluation == "pass_warn":
                reason_lbl = QLabel(
                    "    Insufficient bitstreams — tests passed statistically "
                    "but below recommended sample size"
                )
                reason_lbl.setWordWrap(True)
                reason_lbl.setStyleSheet(
                    f"color: {COLORS['warning']}; font-size: 9pt; "
                    f"padding: 0px 0px 4px 32px; font-style: italic;"
                )
                self.summary_layout.addWidget(reason_lbl)

        self.summary_layout.addStretch()

        # Populate Details tree with all reports
        self.details_tree.clear()
        for test_name, data in all_reports:
            report = data.get("report", data)
            evaluation = _nuanced_eval(report)
            badge_text, _ = _eval_badge(evaluation)
            test_root = QTreeWidgetItem([test_name, "", badge_text])
            self._color_status(test_root, evaluation)
            self.details_tree.addTopLevelItem(test_root)

            for config in report.get("configurations", []):
                config_eval = config.get("evaluation", "inconclusive")
                cb_text, _ = _eval_badge(config_eval)
                config_item = QTreeWidgetItem([
                    f"Configuration {config.get('configuration id', '?')}",
                    "", cb_text
                ])
                self._color_status(config_item, config_eval)
                test_root.addChild(config_item)

                for test in config.get("tests", []):
                    test_eval = test.get("evaluation", "inconclusive")
                    t_badge, _ = _eval_badge(test_eval)
                    test_item = QTreeWidgetItem([
                        f"Test {test.get('test id', '?')}", "", t_badge
                    ])
                    self._color_status(test_item, test_eval)
                    config_item.addChild(test_item)

                    for calc in test.get("calculations", []):
                        calc_item = QTreeWidgetItem([
                            calc.get("name", ""), calc.get("value", ""), ""
                        ])
                        test_item.addChild(calc_item)

                    for crit in test.get("criteria", []):
                        result = crit.get("result", False)
                        crit_item = QTreeWidgetItem([
                            crit.get("criterion", ""), "",
                            "PASS" if result else "FAIL"
                        ])
                        self._color_status(crit_item, "pass" if result else "fail")
                        test_item.addChild(crit_item)

                config_item.setExpanded(True)
            test_root.setExpanded(True)

        # Populate JSON tab with combined reports
        if all_reports:
            combined = [data for _, data in all_reports]
            self.json_view.setPlainText(json.dumps(
                combined if len(combined) > 1 else combined[0], indent=4
            ))

    def _build_summary(self, report: dict):
        self._clear_summary()

        # Evaluation badge — use nuanced evaluation
        evaluation = _nuanced_eval(report)
        badge_text, badge_color = _eval_badge(evaluation)
        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            font-size: 20pt; font-weight: bold; color: {badge_color};
            padding: 20px; background-color: {COLORS['bg_tertiary']};
            border-radius: 8px; border: 2px solid {badge_color};
        """)
        badge.setToolTip(
            "Statistical tests passed but insufficient sample size"
            if evaluation == "pass_warn" else ""
        )
        self.summary_layout.addWidget(badge)

        # Show warning note for pass_warn
        if evaluation == "pass_warn":
            warn_lbl = QLabel(
                "⚠ Statistical tests passed, but sample size is below the "
                "recommended minimum. Increase the number of bitstreams for "
                "a definitive result."
            )
            warn_lbl.setWordWrap(True)
            warn_lbl.setStyleSheet(
                f"color: {COLORS['warning']}; padding: 4px 8px; font-style: italic;"
            )
            self.summary_layout.addWidget(warn_lbl)

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
