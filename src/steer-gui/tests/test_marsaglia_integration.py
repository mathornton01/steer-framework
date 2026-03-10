"""
Unit tests for the 13 remaining Diehard Marsaglia tests in the STEER GUI framework.

Tests cover:
1. Test registry discovery
2. GUI editable parameter definitions
3. C source file structural validation
4. Test documentation completeness
5. Warnings for suspect/deprecated tests
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
FRAMEWORK_ROOT = str(Path(__file__).parent.parent.parent.parent)

# The 13 new Marsaglia tests
MARSAGLIA_TESTS = [
    ("rank-32x32", "rank_32x32.c", "diehard_rank_32x32_test", "rank 32x32"),
    ("rank-6x8", "rank_6x8.c", "diehard_rank_6x8_test", "rank 6x8"),
    ("bitstream", "bitstream.c", "diehard_bitstream_test", "bitstream"),
    ("opso", "opso.c", "diehard_opso_test", "opso"),
    ("oqso", "oqso.c", "diehard_oqso_test", "oqso"),
    ("dna", "dna.c", "diehard_dna_test", "dna"),
    ("count-1s-stream", "count_1s_stream.c", "diehard_count_1s_stream_test", "count 1s stream"),
    ("count-1s-byte", "count_1s_byte.c", "diehard_count_1s_byte_test", "count 1s byte"),
    ("3dsphere", "3dsphere.c", "diehard_3dsphere_test", "3dsphere"),
    ("sums", "sums.c", "diehard_sums_test", "sums"),
    ("runs", "runs.c", "diehard_runs_test", "runs"),
    ("craps", "craps.c", "diehard_craps_test", "craps"),
    ("marsaglia-tsang-gcd", "marsaglia_tsang_gcd.c", "diehard_marsaglia_tsang_gcd_test", "marsaglia tsang gcd"),
]

DOC_KEYS = [
    "rank_32x32", "rank_6x8", "bitstream", "opso", "oqso", "dna",
    "count_1s_stream", "count_1s_byte", "3dsphere", "sums", "runs",
    "craps", "marsaglia_tsang_gcd",
]


class TestMarsagliaRegistry(unittest.TestCase):
    """Test that all 13 new Marsaglia tests are discovered."""

    def setUp(self):
        from test_registry import TestRegistry
        self.registry = TestRegistry(FRAMEWORK_ROOT)

    def test_all_28_diehard_tests(self):
        """Total Diehard count should be 28."""
        dh = self.registry.diehard_tests()
        self.assertEqual(len(dh), 28, f"Expected 28, got {len(dh)}")

    def test_marsaglia_tests_present(self):
        """All 13 new Marsaglia tests should be in the registry."""
        dh = {t.program_name for t in self.registry.diehard_tests()}
        for _, _, prog_name, _ in MARSAGLIA_TESTS:
            self.assertIn(prog_name, dh, f"Missing test: {prog_name}")

    def test_display_names_title_case(self):
        """Display names should be title case."""
        for test in self.registry.diehard_tests():
            self.assertEqual(test.display_name, test.display_name.title(),
                             f"Not title case: {test.display_name}")

    def test_test_type(self):
        """All should have test_type 'diehard'."""
        for test in self.registry.diehard_tests():
            self.assertEqual(test.test_type, "diehard")


class TestMarsagliaEditableParams(unittest.TestCase):
    """Test GUI editable parameter definitions."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def test_3dsphere_params(self):
        """3dsphere should have num points param."""
        params = self.params["diehard_3dsphere"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "num points")
        self.assertEqual(params[0]["default"], 4000)

    def test_craps_params(self):
        """Craps should have num games param."""
        params = self.params["diehard_craps"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "num games")
        self.assertEqual(params[0]["default"], 200000)

    def test_gcd_params(self):
        """Marsaglia-Tsang GCD should have num pairs param."""
        params = self.params["diehard_marsaglia_tsang_gcd"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "num pairs")
        self.assertEqual(params[0]["default"], 10000)

    def test_no_params_tests(self):
        """Tests without extra params should not appear in TEST_EDITABLE_PARAMS."""
        no_param_prefixes = [
            "diehard_rank_32x32", "diehard_rank_6x8", "diehard_bitstream",
            "diehard_opso", "diehard_oqso", "diehard_dna",
            "diehard_count_1s_stream", "diehard_count_1s_byte",
            "diehard_sums", "diehard_runs",
        ]
        for prefix in no_param_prefixes:
            self.assertNotIn(prefix, self.params,
                             f"{prefix} should not have test-specific params")

    def test_defaults_within_range(self):
        """Default values should be within [min, max]."""
        marsaglia_prefixes = ["diehard_3dsphere", "diehard_craps", "diehard_marsaglia_tsang_gcd"]
        for prefix in marsaglia_prefixes:
            for pdef in self.params[prefix]:
                self.assertGreaterEqual(pdef["default"], pdef["min"])
                self.assertLessEqual(pdef["default"], pdef["max"])


class TestMarsagliaPrefixMatching(unittest.TestCase):
    """Test prefix matching for parameter lookup."""

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

    def test_3dsphere_match(self):
        params = self._get_editable_params("diehard_3dsphere_test")
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "num points")

    def test_craps_match(self):
        params = self._get_editable_params("diehard_craps_test")
        self.assertEqual(len(params), 1)

    def test_gcd_match(self):
        params = self._get_editable_params("diehard_marsaglia_tsang_gcd_test")
        self.assertEqual(len(params), 1)

    def test_no_param_tests_empty(self):
        """Tests without params should return empty."""
        for name in ["diehard_rank_32x32_test", "diehard_bitstream_test",
                     "diehard_opso_test", "diehard_runs_test", "diehard_sums_test"]:
            params = self._get_editable_params(name)
            self.assertEqual(len(params), 0, f"Expected no params for {name}")


class TestMarsagliaCSourceFiles(unittest.TestCase):
    """Validate structural correctness of C source files."""

    def test_source_files_exist(self):
        """All 13 C source files should exist."""
        for dirname, filename, _, _ in MARSAGLIA_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            self.assertTrue(path.exists(), f"Missing: {path}")

    def test_program_name_correct(self):
        """Each C file should define the correct PROGRAM_NAME."""
        for dirname, filename, expected_name, _ in MARSAGLIA_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text()
            self.assertIn(expected_name, content,
                          f"Wrong PROGRAM_NAME in {filename}")

    def test_steer_callbacks_present(self):
        """Each C file must implement all required STEER callbacks."""
        required = [
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
        for dirname, filename, _, _ in MARSAGLIA_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text()
            for func in required:
                self.assertIn(func, content, f"Missing '{func}' in {filename}")

    def test_required_includes(self):
        """Each C file should include required STEER headers."""
        required_includes = ['#include "steer.h"', '#include "steer_test_shell.h"', '#include "cephes.h"']
        for dirname, filename, _, _ in MARSAGLIA_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text()
            for inc in required_includes:
                self.assertIn(inc, content, f"Missing '{inc}' in {filename}")

    def test_marsaglia_credited(self):
        """Each file should credit George Marsaglia."""
        for dirname, filename, _, _ in MARSAGLIA_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text()
            self.assertIn("Marsaglia", content, f"Missing Marsaglia credit in {filename}")

    def test_test_specific_params_in_c(self):
        """C files with test-specific params should parse them."""
        param_checks = {
            "3dsphere.c": "num points",
            "craps.c": "num games",
            "marsaglia_tsang_gcd.c": "num pairs",
        }
        for dirname, filename, _, _ in MARSAGLIA_TESTS:
            if filename not in param_checks:
                continue
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text()
            self.assertIn(f'"{param_checks[filename]}"', content,
                          f"Missing param '{param_checks[filename]}' in {filename}")

    def test_suspect_warnings(self):
        """Suspect tests (opso, oqso, dna) should contain warnings."""
        suspect_tests = [
            ("opso", "opso.c"),
            ("oqso", "oqso.c"),
            ("dna", "dna.c"),
        ]
        for dirname, filename in suspect_tests:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"Not found: {path}")
            content = path.read_text().lower()
            self.assertTrue(
                "warning" in content or "suspect" in content,
                f"{filename} should contain a suspect warning")

    def test_sums_deprecated_warning(self):
        """sums.c should contain a DO NOT USE warning."""
        path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / "sums" / "sums.c"
        if not path.exists():
            self.skipTest("sums.c not found")
        content = path.read_text()
        self.assertTrue(
            "DO NOT USE" in content or "deprecated" in content.lower(),
            "sums.c should contain a DO NOT USE/deprecated warning")


class TestMarsagliaDocumentation(unittest.TestCase):
    """Test documentation completeness."""

    def setUp(self):
        doc_path = Path(FRAMEWORK_ROOT) / "docs" / "tests" / "test_documentation.json"
        with open(doc_path) as f:
            self.docs = json.load(f)
        self.tests = self.docs["tests"]

    def test_all_documented(self):
        """All 13 tests should have documentation entries."""
        for key in DOC_KEYS:
            self.assertIn(key, self.tests, f"Missing docs for '{key}'")

    def test_doc_fields_complete(self):
        """Each entry should have all required fields."""
        required_fields = [
            "name", "category", "program_name", "summary",
            "description", "mathematical_basis", "parameters",
            "interpretation", "recommendations", "example_applications",
        ]
        for key in DOC_KEYS:
            if key not in self.tests:
                self.skipTest(f"'{key}' not in docs")
            for field in required_fields:
                self.assertIn(field, self.tests[key],
                              f"Missing '{field}' in docs for '{key}'")

    def test_program_names_match(self):
        """Documentation program_names should match registry convention."""
        expected = {
            "rank_32x32": "diehard_rank_32x32_test",
            "rank_6x8": "diehard_rank_6x8_test",
            "bitstream": "diehard_bitstream_test",
            "opso": "diehard_opso_test",
            "oqso": "diehard_oqso_test",
            "dna": "diehard_dna_test",
            "count_1s_stream": "diehard_count_1s_stream_test",
            "count_1s_byte": "diehard_count_1s_byte_test",
            "3dsphere": "diehard_3dsphere_test",
            "sums": "diehard_sums_test",
            "runs": "diehard_runs_test",
            "craps": "diehard_craps_test",
            "marsaglia_tsang_gcd": "diehard_marsaglia_tsang_gcd_test",
        }
        for key, prog in expected.items():
            if key not in self.tests:
                continue
            self.assertEqual(self.tests[key]["program_name"], prog)

    def test_category_is_diehard(self):
        """All should be in Diehard category."""
        for key in DOC_KEYS:
            if key not in self.tests:
                continue
            self.assertEqual(self.tests[key]["category"], "Diehard Statistical Test Battery")

    def test_suspect_warnings_in_docs(self):
        """opso, oqso, dna docs should contain suspect warnings."""
        for key in ["opso", "oqso", "dna"]:
            if key not in self.tests:
                continue
            desc = self.tests[key]["description"]
            self.assertTrue(
                "WARNING" in desc or "suspect" in desc.lower(),
                f"{key} docs should contain a suspect warning")

    def test_sums_deprecated_in_docs(self):
        """sums docs should contain DO NOT USE warning."""
        if "sums" not in self.tests:
            self.skipTest("sums not in docs")
        desc = self.tests["sums"]["description"]
        self.assertTrue(
            "DO NOT USE" in desc or "DEPRECATED" in desc or "deprecated" in desc.lower(),
            "sums docs should contain DO NOT USE warning")


class TestMarsagliaTestNamesFile(unittest.TestCase):
    """Test the diehard_test_names.txt file."""

    def setUp(self):
        path = Path(FRAMEWORK_ROOT) / "build_files" / "diehard_test_names.txt"
        self.names = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    def test_total_count(self):
        """Should have 28 test names."""
        self.assertEqual(len(self.names), 28, f"Expected 28, got {len(self.names)}")

    def test_marsaglia_tests_listed(self):
        """All 13 new test names should be present."""
        expected = [t[3] for t in MARSAGLIA_TESTS]
        for name in expected:
            self.assertIn(name, self.names, f"Missing: '{name}'")

    def test_no_duplicates(self):
        """No duplicate test names."""
        self.assertEqual(len(self.names), len(set(self.names)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
