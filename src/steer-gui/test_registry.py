# =================================================================================================
# test_registry.py — Discover available STEER tests from build config files
# =================================================================================================

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SteerTestInfo:
    display_name: str
    program_name: str
    test_type: str  # "nist-sts", "diehard", "testu01", "ais", or "python"
    executable_path: str = ""
    is_available: bool = False
    parameter_templates: dict = field(default_factory=dict)


class TestRegistry:
    """Discovers and catalogs all STEER tests from the build configuration."""

    def __init__(self, framework_root: str):
        self.root = Path(framework_root)
        self.tests: list[SteerTestInfo] = []
        self._discover()

    def _read_names_file(self, filename: str) -> list[str]:
        path = self.root / "build_files" / filename
        if not path.exists():
            return []
        names = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                names.append(line)
        return names

    def _find_executable(self, program_name: str) -> str:
        """Search bin/ for the executable, return path if found."""
        bin_dir = self.root / "bin"
        if not bin_dir.exists():
            return ""
        for dirpath, _, filenames in os.walk(bin_dir):
            if program_name in filenames:
                return str(Path(dirpath) / program_name)
        return ""

    def _find_parameter_templates(self, test_name_dash: str) -> dict:
        """Find parameter JSON files for a test."""
        templates = {}
        param_dir = self.root / "test" / "validation" / "nist-sts" / test_name_dash
        if param_dir.exists():
            for f in sorted(param_dir.glob("parameters_*.json")):
                profile_id = f.stem.replace("parameters_", "")
                templates[profile_id] = str(f)
        return templates

    def _discover(self):
        # NIST STS C tests
        c_names = self._read_names_file("test_names.txt")
        for name in c_names:
            dash_name = name.replace(" ", "-")
            underscore_name = name.replace(" ", "_")
            program_name = f"nist_sts_{underscore_name}_test"
            exe_path = self._find_executable(program_name)
            templates = self._find_parameter_templates(dash_name)
            self.tests.append(SteerTestInfo(
                display_name=name.title(),
                program_name=program_name,
                test_type="nist-sts",
                executable_path=exe_path,
                is_available=bool(exe_path),
                parameter_templates=templates,
            ))

        # Diehard C tests
        dh_names = self._read_names_file("diehard_test_names.txt")
        for name in dh_names:
            dash_name = name.replace(" ", "-")
            underscore_name = name.replace(" ", "_")
            program_name = f"diehard_{underscore_name}_test"
            exe_path = self._find_executable(program_name)
            templates = self._find_parameter_templates(dash_name)
            self.tests.append(SteerTestInfo(
                display_name=name.title(),
                program_name=program_name,
                test_type="diehard",
                executable_path=exe_path,
                is_available=bool(exe_path),
                parameter_templates=templates,
            ))

        # TestU01 C tests
        tu01_names = self._read_names_file("testu01_test_names.txt")
        for name in tu01_names:
            dash_name = name.replace(" ", "-")
            underscore_name = name.replace(" ", "_")
            program_name = f"testu01_{underscore_name}_test"
            exe_path = self._find_executable(program_name)
            templates = self._find_parameter_templates(dash_name)
            self.tests.append(SteerTestInfo(
                display_name=name.title(),
                program_name=program_name,
                test_type="testu01",
                executable_path=exe_path,
                is_available=bool(exe_path),
                parameter_templates=templates,
            ))

        # AIS 20/31 tests
        ais_names = self._read_names_file("ais_test_names.txt")
        for name in ais_names:
            dash_name = name.replace(" ", "-")
            underscore_name = name.replace(" ", "_")
            program_name = f"{underscore_name}_test"
            exe_path = self._find_executable(program_name)
            templates = self._find_parameter_templates(dash_name)
            self.tests.append(SteerTestInfo(
                display_name=name.title(),
                program_name=program_name,
                test_type="ais",
                executable_path=exe_path,
                is_available=bool(exe_path),
                parameter_templates=templates,
            ))

        # Python tests
        py_names = self._read_names_file("python_test_names.txt")
        for name in py_names:
            dash_name = name.replace(" ", "-")
            underscore_name = name.replace(" ", "_")
            program_name = f"{underscore_name}_test"
            exe_path = self._find_executable(program_name)
            templates = self._find_parameter_templates(dash_name)
            self.tests.append(SteerTestInfo(
                display_name=name.title(),
                program_name=program_name,
                test_type="python",
                executable_path=exe_path,
                is_available=bool(exe_path),
                parameter_templates=templates,
            ))

    def get_validation_data_files(self) -> dict[str, str]:
        """Return available validation data files: {profile_id: path}."""
        data_dir = self.root / "data" / "validation" / "nist-sts"
        files = {}
        if data_dir.exists():
            for f in sorted(data_dir.glob("*.bin")):
                files[f.stem] = str(f)
        return files

    def nist_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.test_type == "nist-sts"]

    def diehard_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.test_type == "diehard"]

    def testu01_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.test_type == "testu01"]

    def ais_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.test_type == "ais"]

    def python_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.test_type == "python"]

    def available_tests(self) -> list[SteerTestInfo]:
        return [t for t in self.tests if t.is_available]
