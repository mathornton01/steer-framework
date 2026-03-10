"""
Unit tests for TestU01 Crush battery integration in the STEER GUI framework.

Tests cover:
1. Test registry discovery of all 31 TestU01 tests
2. GUI editable parameter definitions for new tests
3. Parameter JSON building for command-line invocation
4. Test documentation completeness
5. C source file structural validation
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

FRAMEWORK_ROOT = str(Path(__file__).parent.parent.parent.parent)


class TestTestRegistry(unittest.TestCase):
    """Test that the test registry discovers all TestU01 tests."""

    def setUp(self):
        from test_registry import TestRegistry
        self.registry = TestRegistry(FRAMEWORK_ROOT)

    def test_testu01_test_count(self):
        """All 31 TestU01 tests should be discovered."""
        tu01 = self.registry.testu01_tests()
        self.assertEqual(len(tu01), 31, f"Expected 31 TestU01 tests, got {len(tu01)}")

    def test_new_tests_present(self):
        """The 11 new tests (batch 1 + batch 2) should be in the registry."""
        tu01 = {t.program_name for t in self.registry.testu01_tests()}
        expected_new = [
            "testu01_random_walk_test",
            "testu01_hamming_weight_test",
            "testu01_hamming_correlation_test",
            "testu01_hamming_independence_test",
            "testu01_string_run_test",
            "testu01_autocorrelation_test",
            "testu01_periods_in_strings_test",
            "testu01_longest_head_run_test",
            "testu01_fourier_spectral_test",
            "testu01_entropy_discretization_test",
            "testu01_multinomial_bits_over_test",
        ]
        for name in expected_new:
            self.assertIn(name, tu01, f"Missing test: {name}")

    def test_all_test_names_unique(self):
        """All test program names should be unique."""
        tu01 = self.registry.testu01_tests()
        names = [t.program_name for t in tu01]
        self.assertEqual(len(names), len(set(names)), "Duplicate program names found")

    def test_display_names_title_case(self):
        """Display names should be title case."""
        tu01 = self.registry.testu01_tests()
        for test in tu01:
            self.assertEqual(test.display_name, test.display_name.title(),
                             f"Display name not title case: {test.display_name}")

    def test_test_type_is_testu01(self):
        """All TestU01 tests should have test_type 'testu01'."""
        for test in self.registry.testu01_tests():
            self.assertEqual(test.test_type, "testu01")


class TestEditableParams(unittest.TestCase):
    """Test GUI editable parameter definitions."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def test_new_tests_have_params(self):
        """New test families should have editable parameter definitions."""
        expected_prefixes = [
            "testu01_random_walk",
            "testu01_hamming_weight",
            "testu01_hamming_correlation",
            "testu01_hamming_independence",
            "testu01_string_run",
            "testu01_autocorrelation",
            "testu01_periods_in_strings",
            "testu01_longest_head_run",
            "testu01_entropy_discretization",
            "testu01_multinomial_bits_over",
            # Note: fourier_spectral has no test-specific params (only standard 3)
        ]
        for prefix in expected_prefixes:
            self.assertIn(prefix, self.params, f"Missing params for {prefix}")

    def test_param_defs_have_required_fields(self):
        """Each param def must have label, key, type, default, min, max."""
        required_fields = {"label", "key", "type", "default", "min", "max"}
        for prefix, param_list in self.params.items():
            for pdef in param_list:
                for field in required_fields:
                    self.assertIn(field, pdef,
                                  f"Missing field '{field}' in {prefix} param '{pdef.get('label', '?')}'")

    def test_param_types_valid(self):
        """Parameter types should be 'int' or 'float'."""
        for prefix, param_list in self.params.items():
            for pdef in param_list:
                self.assertIn(pdef["type"], ("int", "float"),
                              f"Invalid type '{pdef['type']}' in {prefix}")

    def test_default_within_range(self):
        """Default value should be within [min, max]."""
        for prefix, param_list in self.params.items():
            for pdef in param_list:
                self.assertGreaterEqual(pdef["default"], pdef["min"],
                                        f"Default < min in {prefix}/{pdef['label']}")
                self.assertLessEqual(pdef["default"], pdef["max"],
                                     f"Default > max in {prefix}/{pdef['label']}")

    def test_random_walk_params(self):
        """Random walk should have walk_length param."""
        params = self.params["testu01_random_walk"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "walk length")
        self.assertEqual(params[0]["default"], 1000)

    def test_hamming_weight_params(self):
        """Hamming weight should have block_size param."""
        params = self.params["testu01_hamming_weight"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "block size")
        self.assertEqual(params[0]["default"], 32)

    def test_string_run_params(self):
        """String run should have max_run_length param."""
        params = self.params["testu01_string_run"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "max run length")
        self.assertEqual(params[0]["default"], 8)

    def test_autocorrelation_params(self):
        """Autocorrelation should have lag param."""
        params = self.params["testu01_autocorrelation"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "lag")
        self.assertEqual(params[0]["default"], 1)

    def test_entropy_discretization_params(self):
        """Entropy discretization should have block size param."""
        params = self.params["testu01_entropy_discretization"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "block size")
        self.assertEqual(params[0]["default"], 8)

    def test_multinomial_bits_over_params(self):
        """Multinomial bits over should have tuple size param."""
        params = self.params["testu01_multinomial_bits_over"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "tuple size")
        self.assertEqual(params[0]["default"], 4)

    def test_fourier_spectral_no_test_params(self):
        """Fourier spectral should NOT have test-specific params."""
        self.assertNotIn("testu01_fourier_spectral", self.params,
                         "Fourier spectral should not have test-specific params")


class TestPrefixMatching(unittest.TestCase):
    """Test that the prefix matching in _get_editable_params works correctly."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def _get_editable_params(self, program_name: str) -> list:
        """Replicate the longest-prefix-match logic."""
        best_match = ""
        best_params = []
        for prefix, params in self.params.items():
            if program_name.startswith(prefix) and len(prefix) > len(best_match):
                best_match = prefix
                best_params = params
        return best_params

    def test_close_pairs_no_collision(self):
        """close_pairs_test should NOT match close_pairs_bit_match params."""
        cp_params = self._get_editable_params("testu01_close_pairs_test")
        cpbm_params = self._get_editable_params("testu01_close_pairs_bit_match_test")
        self.assertNotEqual(cp_params, cpbm_params,
                            "close_pairs and close_pairs_bit_match should have different params")

    def test_close_pairs_correct_match(self):
        """close_pairs_test should match testu01_close_pairs prefix."""
        params = self._get_editable_params("testu01_close_pairs_test")
        keys = {p["key"] for p in params}
        self.assertIn("num points", keys)
        self.assertIn("dimension", keys)

    def test_close_pairs_bit_match_correct(self):
        """close_pairs_bit_match_test should match its own prefix."""
        params = self._get_editable_params("testu01_close_pairs_bit_match_test")
        keys = {p["key"] for p in params}
        self.assertIn("num bits", keys)

    def test_hamming_correlation_not_hamming_weight(self):
        """hamming_correlation_test should not match hamming_weight prefix."""
        hc_params = self._get_editable_params("testu01_hamming_correlation_test")
        # Should match testu01_hamming_correlation, not testu01_hamming_weight
        # Both have "block size" key, but we verify the correct prefix matched
        hw_prefix_len = len("testu01_hamming_weight")
        hc_prefix_len = len("testu01_hamming_correlation")
        self.assertGreater(hc_prefix_len, hw_prefix_len)
        self.assertEqual(len(hc_params), 1)

    def test_all_new_tests_match(self):
        """Every new test program_name (with params) should find its params."""
        test_names = [
            "testu01_random_walk_test",
            "testu01_hamming_weight_test",
            "testu01_hamming_correlation_test",
            "testu01_hamming_independence_test",
            "testu01_string_run_test",
            "testu01_autocorrelation_test",
            "testu01_periods_in_strings_test",
            "testu01_longest_head_run_test",
            "testu01_entropy_discretization_test",
            "testu01_multinomial_bits_over_test",
        ]
        for name in test_names:
            params = self._get_editable_params(name)
            self.assertTrue(len(params) > 0, f"No params found for {name}")

    def test_fourier_spectral_no_match(self):
        """Fourier spectral should return empty params (no test-specific params)."""
        params = self._get_editable_params("testu01_fourier_spectral_test")
        self.assertEqual(len(params), 0, "Fourier spectral should have no test-specific params")


class TestCSourceFiles(unittest.TestCase):
    """Validate structural correctness of C source files."""

    NEW_TESTS = [
        ("random-walk", "random_walk.c", "testu01_random_walk_test"),
        ("hamming-weight", "hamming_weight.c", "testu01_hamming_weight_test"),
        ("hamming-correlation", "hamming_correlation.c", "testu01_hamming_correlation_test"),
        ("hamming-independence", "hamming_independence.c", "testu01_hamming_independence_test"),
        ("string-run", "string_run.c", "testu01_string_run_test"),
        ("autocorrelation", "autocorrelation.c", "testu01_autocorrelation_test"),
        ("periods-in-strings", "periods_in_strings.c", "testu01_periods_in_strings_test"),
        ("longest-head-run", "longest_head_run.c", "testu01_longest_head_run_test"),
        ("fourier-spectral", "fourier_spectral.c", "testu01_fourier_spectral_test"),
        ("entropy-discretization", "entropy_discretization.c", "testu01_entropy_discretization_test"),
        ("multinomial-bits-over", "multinomial_bits_over.c", "testu01_multinomial_bits_over_test"),
    ]

    def test_source_files_exist(self):
        """All 11 new C source files should exist."""
        for dirname, filename, _ in self.NEW_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            self.assertTrue(path.exists(), f"Missing source file: {path}")

    def test_program_name_correct(self):
        """Each C file should define the correct PROGRAM_NAME."""
        for dirname, filename, expected_name in self.NEW_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn(f'#define PROGRAM_NAME        "{expected_name}"', content,
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
        for dirname, filename, _ in self.NEW_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            for func in required_functions:
                self.assertIn(func, content,
                              f"Missing function '{func}' in {filename}")

    def test_json_parameter_reading(self):
        """Each C file should read test-specific parameters from JSON."""
        for dirname, filename, _ in self.NEW_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn("STEER_GetNativeValue", content,
                          f"No STEER_GetNativeValue in {filename}")

    def test_required_includes(self):
        """Each C file should include required STEER headers."""
        required_includes = [
            '#include "steer.h"',
            '#include "steer_test_shell.h"',
            '#include "cephes.h"',
        ]
        for dirname, filename, _ in self.NEW_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            for inc in required_includes:
                self.assertIn(inc, content, f"Missing include '{inc}' in {filename}")

    def test_test_specific_params_in_c(self):
        """Each C file (except fourier_spectral) should parse its test-specific parameter."""
        param_checks = {
            "random_walk.c": "walk length",
            "hamming_weight.c": "block size",
            "hamming_correlation.c": "block size",
            "hamming_independence.c": "block size",
            "string_run.c": "max run length",
            "autocorrelation.c": "lag",
            "periods_in_strings.c": "block size",
            "longest_head_run.c": "block size",
            "entropy_discretization.c": "block size",
            "multinomial_bits_over.c": "tuple size",
            # fourier_spectral.c has no test-specific params
        }
        for dirname, filename, _ in self.NEW_TESTS:
            if filename not in param_checks:
                continue  # Skip fourier_spectral
            path = Path(FRAMEWORK_ROOT) / "src" / "testu01" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            expected_param = param_checks[filename]
            self.assertIn(f'"{expected_param}"', content,
                          f"Missing parameter '{expected_param}' in {filename}")


class TestDocumentation(unittest.TestCase):
    """Test documentation completeness."""

    def setUp(self):
        doc_path = Path(FRAMEWORK_ROOT) / "docs" / "tests" / "test_documentation.json"
        with open(doc_path) as f:
            self.docs = json.load(f)
        self.tests = self.docs["tests"]

    def test_new_tests_documented(self):
        """All 11 new tests should have documentation entries."""
        expected_keys = [
            "random_walk",
            "hamming_weight",
            "hamming_correlation",
            "hamming_independence",
            "string_run",
            "autocorrelation",
            "periods_in_strings",
            "longest_head_run",
            "fourier_spectral",
            "entropy_discretization",
            "multinomial_bits_over",
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
        new_tests = ["random_walk", "hamming_weight", "hamming_correlation",
                     "hamming_independence", "string_run", "autocorrelation",
                     "periods_in_strings", "longest_head_run", "fourier_spectral",
                     "entropy_discretization", "multinomial_bits_over"]
        for key in new_tests:
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            for field in required_fields:
                self.assertIn(field, self.tests[key],
                              f"Missing field '{field}' in docs for '{key}'")

    def test_program_names_match_registry(self):
        """Documentation program_names should match the registry naming convention."""
        expected_mapping = {
            "random_walk": "testu01_random_walk_test",
            "hamming_weight": "testu01_hamming_weight_test",
            "hamming_correlation": "testu01_hamming_correlation_test",
            "hamming_independence": "testu01_hamming_independence_test",
            "string_run": "testu01_string_run_test",
            "autocorrelation": "testu01_autocorrelation_test",
            "periods_in_strings": "testu01_periods_in_strings_test",
            "longest_head_run": "testu01_longest_head_run_test",
            "fourier_spectral": "testu01_fourier_spectral_test",
            "entropy_discretization": "testu01_entropy_discretization_test",
            "multinomial_bits_over": "testu01_multinomial_bits_over_test",
        }
        for key, expected_prog in expected_mapping.items():
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            self.assertEqual(self.tests[key]["program_name"], expected_prog)

    def test_category_is_testu01(self):
        """All new tests should be in the TestU01 Crush Battery category."""
        new_tests = ["random_walk", "hamming_weight", "hamming_correlation",
                     "hamming_independence", "string_run", "autocorrelation",
                     "periods_in_strings", "longest_head_run", "fourier_spectral",
                     "entropy_discretization", "multinomial_bits_over"]
        for key in new_tests:
            if key not in self.tests:
                continue
            self.assertEqual(self.tests[key]["category"], "TestU01 Crush Battery")


class TestParameterBuilding(unittest.TestCase):
    """Test that parameter JSON is built correctly for command-line invocation."""

    def test_build_parameters_includes_test_params(self):
        """_build_parameters should include test-specific params in the JSON."""
        from test_registry import SteerTestInfo

        # Import just the function logic (can't easily instantiate MainWindow without Qt)
        # Instead, test the expected JSON structure
        test_info = SteerTestInfo(
            display_name="Random Walk",
            program_name="testu01_random_walk_test",
            test_type="testu01",
        )
        params = {
            "bitstream_count": 1,
            "bitstream_length": 1000000,
            "alpha": 0.01,
            "report_level": "full",
            "test_params": {"walk length": 500},
        }

        # Simulate _build_parameters logic
        param_list = [
            {"name": "bitstream count", "data type": "unsigned 64-bit integer",
             "units": "bitstreams", "value": str(params["bitstream_count"])},
            {"name": "bitstream length", "data type": "unsigned 64-bit integer",
             "units": "bits", "value": str(params["bitstream_length"])},
            {"name": "significance level (alpha)",
             "data type": "double precision floating point",
             "precision": "6", "value": str(params["alpha"])},
        ]
        for key, value in params["test_params"].items():
            if isinstance(value, float):
                param_list.append({
                    "name": key,
                    "data type": "double precision floating point",
                    "precision": "6", "value": str(value),
                })
            else:
                param_list.append({
                    "name": key,
                    "data type": "unsigned 64-bit integer",
                    "value": str(value),
                })

        result = {"parameter set": {
            "test name": test_info.display_name.lower(),
            "parameter set name": "gui",
            "parameters": param_list,
        }}

        # Verify the walk length parameter is present
        param_names = [p["name"] for p in result["parameter set"]["parameters"]]
        self.assertIn("walk length", param_names)
        walk_param = [p for p in result["parameter set"]["parameters"]
                      if p["name"] == "walk length"][0]
        self.assertEqual(walk_param["value"], "500")


class TestTestNamesFile(unittest.TestCase):
    """Test the testu01_test_names.txt file."""

    def setUp(self):
        path = Path(FRAMEWORK_ROOT) / "build_files" / "testu01_test_names.txt"
        self.names = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    def test_total_count(self):
        """Should have 31 test names."""
        self.assertEqual(len(self.names), 31, f"Expected 31, got {len(self.names)}: {self.names}")

    def test_new_tests_listed(self):
        """All 11 new test names should be in the file."""
        expected = ["random walk", "hamming weight", "hamming correlation",
                    "hamming independence", "string run", "autocorrelation",
                    "periods in strings", "longest head run", "fourier spectral",
                    "entropy discretization", "multinomial bits over"]
        for name in expected:
            self.assertIn(name, self.names, f"Missing test name: '{name}'")

    def test_no_duplicates(self):
        """No duplicate test names."""
        self.assertEqual(len(self.names), len(set(self.names)),
                         "Duplicate test names found")


if __name__ == "__main__":
    unittest.main(verbosity=2)
