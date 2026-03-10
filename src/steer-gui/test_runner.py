# =================================================================================================
# test_runner.py — Execute STEER tests as subprocesses with Qt signal integration
# =================================================================================================

import json
import os
import platform
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, pyqtSignal


def windows_to_wsl_path(win_path: str) -> str:
    """Convert a Windows path to a WSL-accessible path."""
    p = win_path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p


class TestRunner(QObject):
    """Runs STEER test executables as subprocesses."""

    test_started = pyqtSignal(str)
    test_output = pyqtSignal(str, str)  # test_name, text
    test_completed = pyqtSignal(str, int, str)  # test_name, exit_code, report_path
    test_error = pyqtSignal(str, str)  # test_name, error
    batch_progress = pyqtSignal(int, int)  # completed, total
    batch_completed = pyqtSignal(int, int, int)  # total, passed, failed

    def __init__(self, framework_root: str, parent=None):
        super().__init__(parent)
        self.root = Path(framework_root)
        self._queue: list[dict] = []
        self._current_process: QProcess | None = None
        self._current_test: dict | None = None
        self._results: list[tuple[str, int, str]] = []
        self._total = 0
        self._running = False
        self._use_wsl = platform.system() == "Windows"

    def is_running(self):
        return self._running

    def run_tests(self, test_configs: list[dict]):
        """Start a batch of tests.

        Each config dict: {
            'test_name': str,
            'program_name': str,
            'executable_path': str,
            'test_type': str,  # 'nist-sts' or 'python'
            'entropy_file': str,
            'parameters': dict,  # parsed parameter JSON
            'report_level': str,
        }
        """
        self._queue = list(test_configs)
        self._results = []
        self._total = len(test_configs)
        self._running = True
        self._run_next()

    def stop(self):
        """Stop the current test and clear the queue."""
        self._queue.clear()
        if self._current_process and self._current_process.state() != QProcess.ProcessState.NotRunning:
            self._current_process.kill()
        self._running = False

    def _run_next(self):
        if not self._queue:
            self._running = False
            passed = sum(1 for _, code, _ in self._results if code == 0)
            failed = self._total - passed
            self.batch_completed.emit(self._total, passed, failed)
            return

        config = self._queue.pop(0)
        self._current_test = config
        test_name = config["test_name"]

        self.test_started.emit(test_name)
        self.batch_progress.emit(len(self._results), self._total)

        # Write temporary parameter file
        results_dir = self.root / "results" / "gui"
        results_dir.mkdir(parents=True, exist_ok=True)
        params_dir = results_dir / "params"
        params_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        param_file = params_dir / f"{config['program_name']}_params_{ts}.json"
        param_file.write_text(json.dumps(config["parameters"], indent=4))

        report_file = results_dir / f"{config['program_name']}_{ts}.json"
        config["_report_path"] = str(report_file)
        config["_param_path"] = str(param_file)

        # Build command
        exe_path = config["executable_path"]
        entropy_path = config["entropy_file"]
        level = config.get("report_level", "full")

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._on_stdout)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error)
        self._current_process = process

        if self._use_wsl and config["test_type"] in ("nist-sts", "diehard", "testu01"):
            # Run C tests via WSL
            wsl_exe = windows_to_wsl_path(exe_path)
            wsl_entropy = windows_to_wsl_path(entropy_path)
            wsl_params = windows_to_wsl_path(str(param_file))
            wsl_report = windows_to_wsl_path(str(report_file))

            args = [
                "-d", "Ubuntu-24.04", "--",
                wsl_exe,
                "-l", level,
                "-e", wsl_entropy,
                "-p", wsl_params,
                "-r", wsl_report,
                "-R",
            ]
            process.start("wsl.exe", args)
        elif self._use_wsl and config["test_type"] == "python":
            # Run Python tests via WSL (they need the wrapper script)
            wsl_exe = windows_to_wsl_path(exe_path)
            wsl_entropy = windows_to_wsl_path(entropy_path)
            wsl_params = windows_to_wsl_path(str(param_file))
            wsl_report = windows_to_wsl_path(str(report_file))

            args = [
                "-d", "Ubuntu-24.04", "--",
                "bash", wsl_exe,
                "-l", level,
                "-e", wsl_entropy,
                "-p", wsl_params,
                "-r", wsl_report,
                "-R",
            ]
            process.start("wsl.exe", args)
        else:
            # Native execution (Linux/macOS)
            args = [
                "-l", level,
                "-e", entropy_path,
                "-p", str(param_file),
                "-r", str(report_file),
                "-R",
            ]
            process.start(exe_path, args)

    def _on_stdout(self):
        if self._current_process and self._current_test:
            data = self._current_process.readAllStandardOutput().data().decode(
                "utf-8", errors="replace"
            )
            self.test_output.emit(self._current_test["test_name"], data)

    def _on_finished(self, exit_code, _exit_status):
        if self._current_test:
            test_name = self._current_test["test_name"]
            report_path = self._current_test.get("_report_path", "")
            self._results.append((test_name, exit_code, report_path))
            self.test_completed.emit(test_name, exit_code, report_path)
        self._current_process = None
        self._current_test = None
        self._run_next()

    def _on_error(self, error):
        if self._current_test:
            error_msgs = {
                QProcess.ProcessError.FailedToStart: "Failed to start process",
                QProcess.ProcessError.Crashed: "Process crashed",
                QProcess.ProcessError.Timedout: "Process timed out",
                QProcess.ProcessError.WriteError: "Write error",
                QProcess.ProcessError.ReadError: "Read error",
            }
            msg = error_msgs.get(error, f"Unknown error ({error})")
            self.test_error.emit(self._current_test["test_name"], msg)
