#!/usr/bin/env python3
# =================================================================================================
# main.py — STEER Framework GUI entry point with animated splash screen
# =================================================================================================

import os
import sys
from pathlib import Path


def find_framework_root() -> str:
    """Auto-detect the STEER framework root directory."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "build_files" / "test_names.txt").exists():
            return str(current)
        current = current.parent

    home = Path.home()
    candidates = [
        home / "steer-framework",
        home / "Projects" / "rubin-pearl-steer" / "steer-framework",
    ]
    for c in candidates:
        if (c / "build_files" / "test_names.txt").exists():
            return str(c)

    return ""


def main():
    gui_dir = str(Path(__file__).resolve().parent)
    if gui_dir not in sys.path:
        sys.path.insert(0, gui_dir)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("STEER Framework")
    app.setOrganizationName("STEER")
    app.setStyle("Fusion")

    # Apply dark theme
    from theme import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    # Detect framework root
    root = ""
    if len(sys.argv) > 1 and sys.argv[1] == "--root":
        root = sys.argv[2] if len(sys.argv) > 2 else ""
    if not root:
        root = find_framework_root()
    if not root:
        from PyQt6.QtWidgets import QMessageBox, QFileDialog
        QMessageBox.warning(
            None, "STEER Framework",
            "Could not auto-detect the STEER framework directory.\n"
            "Please select it manually."
        )
        root = QFileDialog.getExistingDirectory(None, "Select STEER Framework Root")
        if not root:
            sys.exit(1)

    # Show splash screen, then reveal main window
    from splash_screen import SplashScreen
    from main_window import MainWindow

    window = MainWindow(root)

    def show_main():
        window.show()

    splash = SplashScreen(on_finished=show_main)
    splash.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
