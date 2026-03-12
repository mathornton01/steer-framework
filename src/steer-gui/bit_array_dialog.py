# =================================================================================================
# bit_array_dialog.py — Clickable bit-position assignment dialog for causal models
# =================================================================================================

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QGroupBox, QGridLayout, QWidget, QSizePolicy, QFrame,
    QDialogButtonBox, QToolTip,
)

from theme import COLORS

# ── Category definitions ──────────────────────────────────────────────────────

CATEGORIES = {
    "treatment": {"label": "T", "color": "#4fc3f7", "name": "Treatment"},
    "outcome":   {"label": "O", "color": "#81c784", "name": "Outcome"},
    "covariate": {"label": "C", "color": "#ffb74d", "name": "Covariate"},
}

# Cycle order when clicking
_CYCLE = ["treatment", "outcome", "covariate"]


# ── Clickable Bit Cell ────────────────────────────────────────────────────────

class BitCell(QPushButton):
    """A single clickable cell representing one bit position in a block."""

    role_changed = pyqtSignal(int, str)  # (position_index, new_role)

    def __init__(self, index: int, role: str = "covariate", parent=None):
        super().__init__(parent)
        self._index = index
        self._role = role
        self.setFixedSize(44, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self._make_tooltip())
        self.clicked.connect(self._cycle)
        self._apply_style()

    @property
    def role(self) -> str:
        return self._role

    @role.setter
    def role(self, value: str):
        self._role = value
        self._apply_style()
        self.setToolTip(self._make_tooltip())

    def _make_tooltip(self) -> str:
        cat = CATEGORIES[self._role]
        return f"Bit {self._index}: {cat['name']}\nClick to change role"

    def _cycle(self):
        idx = _CYCLE.index(self._role)
        self._role = _CYCLE[(idx + 1) % len(_CYCLE)]
        self._apply_style()
        self.setToolTip(self._make_tooltip())
        self.role_changed.emit(self._index, self._role)

    def _apply_style(self):
        cat = CATEGORIES[self._role]
        bg = cat["color"]
        self.setText(f"{cat['label']}\n{self._index}")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #1a1a2e;
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid {bg};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border-color: white;
            }}
        """)


# ── Bit Array Dialog ──────────────────────────────────────────────────────────

class BitArrayDialog(QDialog):
    """Pop-out dialog for visually assigning bit positions to Treatment,
    Outcome, and Covariate categories for the Pearl and Rubin causal models.

    Parameters
    ----------
    model_name : str
        "pearl" or "rubin" — controls which extra options are shown.
    block_size : int
        Initial subsequence (block) size.
    treatpos : list[int]
        Initial treatment positions.
    outpos : list[int]
        Initial outcome positions.
    extra : dict
        Model-specific extras:
          Pearl: {"state_bits": int, "alphabet_size": int}
          Rubin: {"alphabet_size": int}
    """

    def __init__(self, model_name: str, block_size: int = 6,
                 treatpos: list[int] | None = None,
                 outpos: list[int] | None = None,
                 extra: dict | None = None,
                 parent=None):
        super().__init__(parent)
        self._model = model_name.lower()
        self._block_size = max(2, block_size)
        self._treatpos = list(treatpos) if treatpos else [0, 1]
        self._outpos = list(outpos) if outpos else [2, 3, 4, 5]
        self._extra = dict(extra) if extra else {}
        self._cells: list[BitCell] = []

        self.setWindowTitle(f"Bit Position Assignment — "
                            f"{'Pearl' if self._model == 'pearl' else 'Rubin'} Causal Model")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}
        """)

        self._build_ui()
        self._sync_cells()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        title = QLabel(f"{'Pearl' if self._model == 'pearl' else 'Rubin'} "
                       f"Causal Model — Bit Assignment")
        title.setStyleSheet(f"font-size: 14pt; font-weight: bold; "
                            f"color: {COLORS['accent_light']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "Each block of the bitstream is split into positions. "
            "Click a cell to cycle its role: "
            "<b style='color:#4fc3f7;'>Treatment</b> → "
            "<b style='color:#81c784;'>Outcome</b> → "
            "<b style='color:#ffb74d;'>Covariate</b>."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px;")
        layout.addWidget(desc)

        # Model methodology description
        if self._model == "pearl":
            method_text = (
                "<b>Pearl (PCM):</b> Groups blocks by treatment tuple, normalizes "
                "outcomes by treatment anchor, builds state-transition graphs per "
                "group, and computes pairwise Jaccard similarity as the test "
                "statistic. A Monte Carlo null distribution is simulated to "
                "compute the p-value. <i>Covariates are ignored.</i>"
            )
        else:
            method_text = (
                "<b>Rubin (RCM):</b> Uses covariate positions for propensity "
                "score matching via multinomial logistic regression. Matched "
                "treatment-control pairs are compared by Hamming distance on "
                "outcome positions. <i>Covariates are essential</i> — positions "
                "not assigned to Treatment or Outcome are used for matching."
            )
        method_lbl = QLabel(method_text)
        method_lbl.setWordWrap(True)
        method_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; padding: 6px 4px; "
            f"font-size: 9pt; background: {COLORS['bg_secondary']}; "
            f"border-radius: 4px;"
        )
        layout.addWidget(method_lbl)

        # Block size spinner
        size_row = QHBoxLayout()
        size_lbl = QLabel("Block size (subseqsize):")
        size_lbl.setStyleSheet("font-weight: bold;")
        size_row.addWidget(size_lbl)
        self._size_spin = QSpinBox()
        self._size_spin.setRange(2, 32)
        self._size_spin.setValue(self._block_size)
        self._size_spin.valueChanged.connect(self._on_size_changed)
        self._size_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        size_row.addWidget(self._size_spin)
        size_row.addStretch()
        layout.addLayout(size_row)

        # Bit array grid
        array_group = QGroupBox("Bit Positions")
        self._grid_layout = QGridLayout(array_group)
        self._grid_layout.setSpacing(4)
        layout.addWidget(array_group)
        self._rebuild_grid()

        # Legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(16)
        for key, cat in CATEGORIES.items():
            chip = QLabel(f"  {cat['name']}  ")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setStyleSheet(f"""
                background-color: {cat['color']}; color: #1a1a2e;
                font-weight: bold; border-radius: 4px; padding: 2px 8px;
            """)
            legend_row.addWidget(chip)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Summary label
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; padding: 4px; "
            f"font-style: italic;"
        )
        layout.addWidget(self._summary_label)

        # Model-specific parameters
        model_group = QGroupBox(
            "Pearl Parameters" if self._model == "pearl" else "Rubin Parameters"
        )
        mg_layout = QGridLayout(model_group)
        mg_layout.setSpacing(6)

        if self._model == "pearl":
            mg_layout.addWidget(QLabel("State bits:"), 0, 0)
            self._state_bits_spin = QSpinBox()
            self._state_bits_spin.setRange(1, 16)
            self._state_bits_spin.setValue(self._extra.get("state_bits", 2))
            self._state_bits_spin.setStyleSheet(f"""
                QSpinBox {{
                    background: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px; padding: 4px;
                }}
            """)
            mg_layout.addWidget(self._state_bits_spin, 0, 1)

            mg_layout.addWidget(QLabel("Null simulations:"), 2, 0)
            self._sims_spin = QSpinBox()
            self._sims_spin.setRange(10, 10000)
            self._sims_spin.setSingleStep(50)
            self._sims_spin.setValue(self._extra.get("null_simulations", 200))
            self._sims_spin.setStyleSheet(f"""
                QSpinBox {{
                    background: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px; padding: 4px;
                }}
            """)
            mg_layout.addWidget(self._sims_spin, 2, 1)

        mg_layout.addWidget(QLabel("Alphabet size (k):"), 3 if self._model == "pearl" else 1, 0)
        self._k_spin = QSpinBox()
        self._k_spin.setRange(2, 64)
        self._k_spin.setValue(self._extra.get("alphabet_size", 3))
        self._k_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px; padding: 4px;
            }}
        """)
        mg_layout.addWidget(self._k_spin, 3 if self._model == "pearl" else 1, 1)
        mg_layout.setColumnStretch(1, 1)
        layout.addWidget(model_group)

        # Validation / error label
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            f"color: {COLORS['failure']}; font-weight: bold; padding: 4px;"
        )
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # OK / Cancel buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                color: white;
                font-weight: bold;
                padding: 6px 20px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_light']};
            }}
        """)
        layout.addWidget(btn_box)

        self._update_summary()

    def _rebuild_grid(self):
        """Create (or recreate) the clickable bit cells for the current block size."""
        # Remove existing cells
        for cell in self._cells:
            cell.setParent(None)
        self._cells.clear()

        # Clear layout
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # Add index headers
        cols_per_row = min(self._block_size, 16)
        for i in range(self._block_size):
            row = i // cols_per_row
            col = i % cols_per_row

            # Determine initial role
            if i in self._treatpos:
                role = "treatment"
            elif i in self._outpos:
                role = "outcome"
            else:
                role = "covariate"

            cell = BitCell(i, role)
            cell.role_changed.connect(self._on_role_changed)
            self._grid_layout.addWidget(cell, row, col)
            self._cells.append(cell)

    def _sync_cells(self):
        """Rebuild internal position lists from cell state."""
        self._treatpos = [c._index for c in self._cells if c.role == "treatment"]
        self._outpos = [c._index for c in self._cells if c.role == "outcome"]
        self._update_summary()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_size_changed(self, new_size: int):
        old_size = self._block_size
        self._block_size = new_size
        # Trim positions that are now out of range
        self._treatpos = [p for p in self._treatpos if p < new_size]
        self._outpos = [p for p in self._outpos if p < new_size]
        # If we grew, new positions default to covariate (they just won't be in either list)
        if not self._treatpos:
            self._treatpos = [0]
        if not self._outpos:
            self._outpos = [min(1, new_size - 1)]
            # Avoid overlap
            if self._outpos[0] in self._treatpos and new_size > 1:
                for j in range(new_size):
                    if j not in self._treatpos:
                        self._outpos = [j]
                        break
        self._rebuild_grid()
        self._sync_cells()

    def _on_role_changed(self, index: int, new_role: str):
        self._sync_cells()

    def _update_summary(self):
        treat_str = ", ".join(str(p) for p in sorted(self._treatpos)) or "none"
        out_str = ", ".join(str(p) for p in sorted(self._outpos)) or "none"
        covariates = [i for i in range(self._block_size)
                      if i not in self._treatpos and i not in self._outpos]
        cov_str = ", ".join(str(p) for p in covariates) or "none"

        model_label = "Pearl" if self._model == "pearl" else "Rubin"
        text = (
            f"Treatment positions: [{treat_str}]  ·  "
            f"Outcome positions: [{out_str}]"
        )
        if covariates:
            text += f"  ·  Covariate positions: [{cov_str}]"
            if self._model == "pearl":
                text += "\n(Pearl model ignores covariate positions)"
            else:
                text += "\n(Rubin model uses covariates for propensity score matching)"
        self._summary_label.setText(text)

    def _validate(self) -> str | None:
        """Return an error message or None if valid."""
        if not self._treatpos:
            return "At least one Treatment position is required."
        if not self._outpos:
            return "At least one Outcome position is required."
        overlap = set(self._treatpos) & set(self._outpos)
        if overlap:
            return f"Treatment and Outcome must be disjoint. Overlap at: {overlap}"
        return None

    def _on_accept(self):
        err = self._validate()
        if err:
            self._error_label.setText(err)
            self._error_label.setVisible(True)
            return
        self._error_label.setVisible(False)
        self.accept()

    # ── Public Accessors ──────────────────────────────────────────────────────

    def get_result(self) -> dict:
        """Return the user's selections.

        Returns dict with keys:
            block_size, treatpos, outpos, alphabet_size
            and for Pearl: state_bits
        """
        result = {
            "block_size": self._block_size,
            "treatpos": sorted(self._treatpos),
            "outpos": sorted(self._outpos),
            "alphabet_size": self._k_spin.value(),
        }
        if self._model == "pearl":
            result["state_bits"] = self._state_bits_spin.value()
            result["null_simulations"] = self._sims_spin.value()
        return result
