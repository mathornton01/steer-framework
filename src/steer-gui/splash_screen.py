#!/usr/bin/env python3
# =================================================================================================
# splash_screen.py — Animated splash screen for STEER GUI
# =================================================================================================

import math
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty,
    QSequentialAnimationGroup, QPauseAnimation, QParallelAnimationGroup,
)
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPainterPath, QTransform
from PyQt6.QtWidgets import QWidget

from theme import COLORS


class SplashScreen(QWidget):
    """Animated splash screen with steering-wheel logo rotation."""

    def __init__(self, on_finished=None):
        super().__init__()
        self._on_finished = on_finished
        self._rotation = 0.0
        self._opacity = 0.0
        self._text_opacity = 0.0
        self._fade_out = 1.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 340)

        # Load logo
        logo_path = Path(__file__).parent / "resources" / "steer-blue-logo.png"
        self._logo = QPixmap(str(logo_path))
        if self._logo.isNull():
            self._logo = QPixmap(600, 100)
            self._logo.fill(QColor(COLORS["accent"]))

        self._setup_animations()

    # ── Animated properties ───────────────────────────────────────────────────

    def _get_rotation(self):
        return self._rotation

    def _set_rotation(self, val):
        self._rotation = val
        self.update()

    rotation = pyqtProperty(float, _get_rotation, _set_rotation)

    def _get_opacity(self):
        return self._opacity

    def _set_opacity(self, val):
        self._opacity = val
        self.update()

    logoOpacity = pyqtProperty(float, _get_opacity, _set_opacity)

    def _get_text_opacity(self):
        return self._text_opacity

    def _set_text_opacity(self, val):
        self._text_opacity = val
        self.update()

    textOpacity = pyqtProperty(float, _get_text_opacity, _set_text_opacity)

    def _get_fade_out(self):
        return self._fade_out

    def _set_fade_out(self, val):
        self._fade_out = val
        self.update()

    fadeOut = pyqtProperty(float, _get_fade_out, _set_fade_out)

    # ── Animation sequence ────────────────────────────────────────────────────

    def _setup_animations(self):
        self._group = QSequentialAnimationGroup(self)

        # Phase 1: Logo fades in while doing a subtle rotation (like turning a steering wheel)
        phase1 = QParallelAnimationGroup()

        fade_in = QPropertyAnimation(self, b"logoOpacity")
        fade_in.setDuration(600)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        phase1.addAnimation(fade_in)

        # Steering wheel motion: rotate right, back through center, slight left, settle
        steer = QPropertyAnimation(self, b"rotation")
        steer.setDuration(1000)
        steer.setStartValue(0.0)
        steer.setEndValue(0.0)
        steer.setKeyValueAt(0.0, -8.0)
        steer.setKeyValueAt(0.25, 5.0)
        steer.setKeyValueAt(0.55, -3.0)
        steer.setKeyValueAt(0.80, 1.0)
        steer.setKeyValueAt(1.0, 0.0)
        steer.setEasingCurve(QEasingCurve.Type.OutQuad)
        phase1.addAnimation(steer)

        self._group.addAnimation(phase1)

        # Phase 2: Brief pause at full display
        self._group.addAnimation(QPauseAnimation(200))

        # Phase 3: Subtitle text fades in
        text_in = QPropertyAnimation(self, b"textOpacity")
        text_in.setDuration(500)
        text_in.setStartValue(0.0)
        text_in.setEndValue(1.0)
        text_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._group.addAnimation(text_in)

        # Phase 4: Hold
        self._group.addAnimation(QPauseAnimation(800))

        # Phase 5: Fade everything out
        fade_out = QPropertyAnimation(self, b"fadeOut")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._group.addAnimation(fade_out)

        self._group.finished.connect(self._finished)

    def start(self):
        """Show the splash screen and begin animation."""
        self._center_on_screen()
        self.show()
        self._group.start()

    def _center_on_screen(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)

    def _finished(self):
        self.close()
        if self._on_finished:
            self._on_finished()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Master fade
        p.setOpacity(self._fade_out)

        w, h = self.width(), self.height()

        # Background card with rounded corners
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 20, 20)
        p.setClipPath(path)

        # Background
        p.fillRect(0, 0, w, h, QColor(COLORS["bg_primary"]))

        # Subtle gradient overlay at top
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, 0, h * 0.5)
        grad.setColorAt(0, QColor(43, 87, 151, 30))  # accent tint
        grad.setColorAt(1, QColor(43, 87, 151, 0))
        p.fillRect(0, 0, w, int(h * 0.5), grad)

        # Logo — draw rotated around its center
        p.setOpacity(self._fade_out * self._opacity)
        logo_w = min(420, self._logo.width())
        scaled = self._logo.scaledToWidth(logo_w, Qt.TransformationMode.SmoothTransformation)
        logo_x = (w - scaled.width()) / 2
        logo_y = (h - scaled.height()) / 2 - 30

        p.save()
        cx = logo_x + scaled.width() / 2
        cy = logo_y + scaled.height() / 2
        p.translate(cx, cy)
        p.rotate(self._rotation)
        p.translate(-cx, -cy)
        p.drawPixmap(int(logo_x), int(logo_y), scaled)
        p.restore()

        # Subtitle text
        p.setOpacity(self._fade_out * self._text_opacity)
        p.setPen(QColor(COLORS["text_secondary"]))
        font = QFont("Segoe UI", 10)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3.0)
        p.setFont(font)
        text_rect = QRectF(0, logo_y + scaled.height() + 20, w, 30)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "STATISTICAL TESTING OF ENTROPY")

        # Memorial text
        p.setOpacity(self._fade_out * self._text_opacity * 0.7)
        p.setPen(QColor(COLORS["text_secondary"]))
        memorial_font = QFont("Segoe UI", 9)
        memorial_font.setItalic(True)
        p.setFont(memorial_font)
        memorial_rect = QRectF(0, h - 62, w, 20)
        p.drawText(memorial_rect, Qt.AlignmentFlag.AlignCenter, "In Memory of Gary Woodcock.")

        # Version text
        p.setOpacity(self._fade_out * self._text_opacity * 0.5)
        p.setPen(QColor(COLORS["text_muted"]))
        small_font = QFont("Segoe UI", 8)
        p.setFont(small_font)
        ver_rect = QRectF(0, h - 40, w, 20)
        p.drawText(ver_rect, Qt.AlignmentFlag.AlignCenter, "v1.0.0")

        # Accent line under logo
        p.setOpacity(self._fade_out * self._opacity * 0.6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLORS["accent_highlight"]))
        line_w = int(scaled.width() * 0.3)
        line_x = (w - line_w) // 2
        line_y = int(logo_y + scaled.height() + 8)
        p.drawRoundedRect(line_x, line_y, line_w, 3, 1.5, 1.5)

        p.end()
