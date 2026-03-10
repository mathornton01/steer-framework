"""
Unit tests for Dieharder RGB (Robert G. Brown) test integration in the STEER GUI framework.

Tests cover:
1. Test registry discovery of all 15 Diehard tests (5 original + 5 DAB + 5 RGB)
2. GUI editable parameter definitions for RGB tests
3. C source file structural validation
4. Test documentation completeness
5. Prefix matching for parameter lookup
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

FRAMEWORK_ROOT = str(Path(__file__).parent.parent.parent.parent)


class TestDiehardRegistryWithRgb(unittest.TestCase):
    """Test that the test registry discovers all Diehard tests including RGB."""

    def setUp(self):
        from test_registry import TestRegistry
        self.registry = TestRegistry(FRAMEWORK_ROOT)

    def test_diehard_test_count(self):
        """All 28 Diehard tests should be discovered."""
        dh = self.registry.diehard_tests()
        self.assertEqual(len(dh), 28, f"Expected 28 Diehard tests, got {len(dh)}")

    def test_rgb_tests_present(self):
        """All 5 RGB tests should be in the registry."""
        dh = {t.program_name for t in self.registry.diehard_tests()}
        expected_rgb = [
            "diehard_rgb_bitdist_test",
            "diehard_rgb_minimum_distance_test",
            "diehard_rgb_permutations_test",
            "diehard_rgb_lagged_sum_test",
            "diehard_rgb_kstest_test",
        ]
        for name in expected_rgb:
            self.assertIn(name, dh, f"Missing test: {name}")

    def test_all_test_names_unique(self):
        """All test program names should be unique."""
        dh = self.registry.diehard_tests()
        names = [t.program_name for t in dh]
        self.assertEqual(len(names), len(set(names)), "Duplicate program names found")

    def test_display_names_title_case(self):
        """Display names should be title case."""
        for test in self.registry.diehard_tests():
            self.assertEqual(test.display_name, test.display_name.title(),
                             f"Display name not title case: {test.display_name}")

    def test_test_type_is_diehard(self):
        """All Diehard tests should have test_type 'diehard'."""
        for test in self.registry.diehard_tests():
            self.assertEqual(test.test_type, "diehard")


class TestRgbEditableParams(unittest.TestCase):
    """Test GUI editable parameter definitions for RGB tests."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def test_rgb_tests_with_params(self):
        """RGB tests with test-specific params should have definitions."""
        expected_prefixes = [
            "diehard_rgb_bitdist",
            "diehard_rgb_minimum_distance",
            "diehard_rgb_permutations",
            "diehard_rgb_lagged_sum",
            # rgb_kstest has no test-specific params
        ]
        for prefix in expected_prefixes:
            self.assertIn(prefix, self.params, f"Missing params for {prefix}")

    def test_kstest_no_test_params(self):
        """rgb_kstest should NOT have test-specific params."""
        self.assertNotIn("diehard_rgb_kstest", self.params,
                         "rgb_kstest should not have test-specific params")

    def test_param_defs_have_required_fields(self):
        """Each RGB param def must have label, key, type, default, min, max."""
        required_fields = {"label", "key", "type", "default", "min", "max"}
        rgb_prefixes = [k for k in self.params if k.startswith("diehard_rgb_")]
        for prefix in rgb_prefixes:
            for pdef in self.params[prefix]:
                for field in required_fields:
                    self.assertIn(field, pdef,
                                  f"Missing field '{field}' in {prefix} param '{pdef.get('label', '?')}'")

    def test_rgb_bitdist_params(self):
        """RGB Bitdist should have ntuple param."""
        params = self.params["diehard_rgb_bitdist"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "ntuple")
        self.assertEqual(params[0]["default"], 8)

    def test_rgb_minimum_distance_params(self):
        """RGB Minimum Distance should have dimension and num points params."""
        params = self.params["diehard_rgb_minimum_distance"]
        self.assertEqual(len(params), 2)
        keys = {p["key"] for p in params}
        self.assertIn("dimension", keys)
        self.assertIn("num points", keys)

    def test_rgb_permutations_params(self):
        """RGB Permutations should have tuple size param."""
        params = self.params["diehard_rgb_permutations"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "tuple size")
        self.assertEqual(params[0]["default"], 5)

    def test_rgb_lagged_sum_params(self):
        """RGB Lagged Sum should have lag param."""
        params = self.params["diehard_rgb_lagged_sum"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "lag")
        self.assertEqual(params[0]["default"], 0)

    def test_default_within_range(self):
        """Default values should be within [min, max]."""
        rgb_prefixes = [k for k in self.params if k.startswith("diehard_rgb_")]
        for prefix in rgb_prefixes:
            for pdef in self.params[prefix]:
                self.assertGreaterEqual(pdef["default"], pdef["min"],
                                        f"Default < min in {prefix}/{pdef['label']}")
                self.assertLessEqual(pdef["default"], pdef["max"],
                                     f"Default > max in {prefix}/{pdef['label']}")


class TestRgbPrefixMatching(unittest.TestCase):
    """Test prefix matching for RGB test parameter lookup."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def _get_editable_params(self, program_name: str) -> list:
        best_match = ""
        best_params = []
        for prefix, params in self.params.items():
            if program_name.startswith(prefix) and len(prefix) > len(best_match):
                best_match = prefix
                best_params = params
        return best_params

    def test_rgb_tests_with_params_match(self):
        """RGB tests with params should find their params."""
        test_names = [
            "diehard_rgb_bitdist_test",
            "diehard_rgb_minimum_distance_test",
            "diehard_rgb_permutations_test",
            "diehard_rgb_lagged_sum_test",
        ]
        for name in test_names:
            params = self._get_editable_params(name)
            self.assertTrue(len(params) > 0, f"No params found for {name}")

    def test_kstest_no_match(self):
        """rgb_kstest should return empty params."""
        params = self._get_editable_params("diehard_rgb_kstest_test")
        self.assertEqual(len(params), 0, "rgb_kstest should have no test-specific params")

    def test_minimum_distance_not_confused(self):
        """rgb_minimum_distance should not collide with diehard minimum_distance."""
        rgb_params = self._get_editable_params("diehard_rgb_minimum_distance_test")
        # Should have 2 params (dimension + num points)
        self.assertEqual(len(rgb_params), 2)
        keys = {p["key"] for p in rgb_params}
        self.assertIn("dimension", keys)


class TestRgbCSourceFiles(unittest.TestCase):
    """Validate structural correctness of RGB C source files."""

    RGB_TESTS = [
        ("rgb-bitdist", "rgb_bitdist.c", "diehard_rgb_bitdist_test"),
        ("rgb-minimum-distance", "rgb_minimum_distance.c", "diehard_rgb_minimum_distance_test"),
        ("rgb-permutations", "rgb_permutations.c", "diehard_rgb_permutations_test"),
        ("rgb-lagged-sum", "rgb_lagged_sum.c", "diehard_rgb_lagged_sum_test"),
        ("rgb-kstest", "rgb_kstest.c", "diehard_rgb_kstest_test"),
    ]

    def test_source_files_exist(self):
        """All 5 RGB C source files should exist."""
        for dirname, filename, _ in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            self.assertTrue(path.exists(), f"Missing source file: {path}")

    def test_program_name_correct(self):
        """Each C file should define the correct PROGRAM_NAME."""
        for dirname, filename, expected_name in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn(f'#define PROGRAM_NAME', content,
                          f"Missing PROGRAM_NAME in {filename}")
            self.assertIn(expected_name, content,
                          f"Wrong PROGRAM_NAME in {filename}")

    def test_steer_callbacks_present(self):
        """Each C file must implement all required STEER callbacks."""
        required_functions = [
            "char* GetTestInfo(void)",
            "char* GetParametersInfo(void)",
            "int32_t InitTest(",
            "uint32_t GetConfigurationCount(",
            "int32_t SetReport(",
            "int32_t ExecuteTest(",
            "int32_t FinalizeTest(",
            "int main(",
            "STEER_Run(",
        ]
        for dirname, filename, _ in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            for func in required_functions:
                self.assertIn(func, content,
                              f"Missing function '{func}' in {filename}")

    def test_required_includes(self):
        """Each C file should include required STEER headers."""
        required_includes = [
            '#include "steer.h"',
            '#include "steer_test_shell.h"',
            '#include "cephes.h"',
        ]
        for dirname, filename, _ in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            for inc in required_includes:
                self.assertIn(inc, content, f"Missing include '{inc}' in {filename}")

    def test_dieharder_battery_name(self):
        """Each RGB file should reference the Dieharder battery."""
        for dirname, filename, _ in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn("Dieharder", content,
                          f"Missing Dieharder reference in {filename}")

    def test_robert_brown_credited(self):
        """Each RGB file should credit Robert G. Brown as author."""
        for dirname, filename, _ in self.RGB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn("Robert G. Brown", content,
                          f"Missing Robert G. Brown credit in {filename}")

    def test_test_specific_params_in_c(self):
        """RGB C files with test-specific params should parse them."""
        param_checks = {
            "rgb_bitdist.c": "ntuple",
            "rgb_minimum_distance.c": "dimension",
            "rgb_permutations.c": "tuple size",
            "rgb_lagged_sum.c": "lag",
            # rgb_kstest.c has no test-specific params
        }
        for dirname, filename, _ in self.RGB_TESTS:
            if filename not in param_checks:
                continue
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            expected_param = param_checks[filename]
            self.assertIn(f'"{expected_param}"', content,
                          f"Missing parameter '{expected_param}' in {filename}")

    def test_lagged_sum_warning(self):
        """rgb_lagged_sum should include suspect/false positive warning."""
        path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / "rgb-lagged-sum" / "rgb_lagged_sum.c"
        if not path.exists():
            self.skipTest(f"File not found: {path}")
        content = path.read_text()
        self.assertTrue(
            "WARNING" in content or "suspect" in content.lower() or "false positive" in content.lower(),
            "rgb_lagged_sum.c should contain a suspect/false positive warning")


class TestRgbDocumentation(unittest.TestCase):
    """Test documentation completeness for RGB tests."""

    def setUp(self):
        doc_path = Path(FRAMEWORK_ROOT) / "docs" / "tests" / "test_documentation.json"
        with open(doc_path) as f:
            self.docs = json.load(f)
        self.tests = self.docs["tests"]

    def test_rgb_tests_documented(self):
        """All 5 RGB tests should have documentation entries."""
        expected_keys = [
            "rgb_bitdist",
            "rgb_minimum_distance",
            "rgb_permutations",
            "rgb_lagged_sum",
            "rgb_kstest",
        ]
        for key in expected_keys:
            self.assertIn(key, self.tests, f"Missing documentation for '{key}'")

    def test_doc_fields_complete(self):
        """Each documentation entry should have all required fields."""
        required_fields = [
            "name", "category", "program_name", "summary",
            "description", "mathematical_basis", "parameters",
            "interpretation", "recommendations", "example_applications",
        ]
        rgb_tests = ["rgb_bitdist", "rgb_minimum_distance", "rgb_permutations",
                     "rgb_lagged_sum", "rgb_kstest"]
        for key in rgb_tests:
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            for field in required_fields:
                self.assertIn(field, self.tests[key],
                              f"Missing field '{field}' in docs for '{key}'")

    def test_program_names_match_registry(self):
        """Documentation program_names should match the registry naming convention."""
        expected_mapping = {
            "rgb_bitdist": "diehard_rgb_bitdist_test",
            "rgb_minimum_distance": "diehard_rgb_minimum_distance_test",
            "rgb_permutations": "diehard_rgb_permutations_test",
            "rgb_lagged_sum": "diehard_rgb_lagged_sum_test",
            "rgb_kstest": "diehard_rgb_kstest_test",
        }
        for key, expected_prog in expected_mapping.items():
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            self.assertEqual(self.tests[key]["program_name"], expected_prog)

    def test_category_is_rgb(self):
        """All RGB tests should be in the Dieharder RGB Tests category."""
        rgb_tests = ["rgb_bitdist", "rgb_minimum_distance", "rgb_permutations",
                     "rgb_lagged_sum", "rgb_kstest"]
        for key in rgb_tests:
            if key not in self.tests:
                continue
            self.assertEqual(self.tests[key]["category"], "Dieharder RGB Tests")

    def test_lagged_sum_warning_in_docs(self):
        """rgb_lagged_sum documentation should include suspect warning."""
        if "rgb_lagged_sum" not in self.tests:
            self.skipTest("rgb_lagged_sum not in docs")
        desc = self.tests["rgb_lagged_sum"]["description"]
        self.assertTrue(
            "WARNING" in desc or "suspect" in desc.lower() or "false positive" in desc.lower(),
            "rgb_lagged_sum docs should contain a suspect/false positive warning")


class TestDiehardTestNamesFileRgb(unittest.TestCase):
    """Test the diehard_test_names.txt file with RGB additions."""

    def setUp(self):
        path = Path(FRAMEWORK_ROOT) / "build_files" / "diehard_test_names.txt"
        self.names = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    def test_total_count(self):
        """Should have 28 test names."""
        self.assertEqual(len(self.names), 28, f"Expected 28, got {len(self.names)}: {self.names}")

    def test_rgb_tests_listed(self):
        """All 5 RGB test names should be in the file."""
        expected = ["rgb bitdist", "rgb minimum distance", "rgb permutations",
                    "rgb lagged sum", "rgb kstest"]
        for name in expected:
            self.assertIn(name, self.names, f"Missing test name: '{name}'")

    def test_no_duplicates(self):
        """No duplicate test names."""
        self.assertEqual(len(self.names), len(set(self.names)),
                         "Duplicate test names found")


if __name__ == "__main__":
    unittest.main(verbosity=2)
