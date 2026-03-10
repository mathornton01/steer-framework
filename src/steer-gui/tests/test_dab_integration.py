"""
Unit tests for Dieharder DAB (David A. Bauer) test integration in the STEER GUI framework.

Tests cover:
1. Test registry discovery of all 10 Diehard tests (5 original + 5 DAB)
2. GUI editable parameter definitions for DAB tests
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


class TestDiehardRegistry(unittest.TestCase):
    """Test that the test registry discovers all Diehard tests including DAB."""

    def setUp(self):
        from test_registry import TestRegistry
        self.registry = TestRegistry(FRAMEWORK_ROOT)

    def test_diehard_test_count(self):
        """All 28 Diehard tests should be discovered."""
        dh = self.registry.diehard_tests()
        self.assertEqual(len(dh), 28, f"Expected 28 Diehard tests, got {len(dh)}")

    def test_dab_tests_present(self):
        """All 5 DAB tests should be in the registry."""
        dh = {t.program_name for t in self.registry.diehard_tests()}
        expected_dab = [
            "diehard_dab_bytedistrib_test",
            "diehard_dab_dct_test",
            "diehard_dab_filltree_test",
            "diehard_dab_filltree2_test",
            "diehard_dab_monobit2_test",
        ]
        for name in expected_dab:
            self.assertIn(name, dh, f"Missing test: {name}")

    def test_all_test_names_unique(self):
        """All test program names should be unique."""
        dh = self.registry.diehard_tests()
        names = [t.program_name for t in dh]
        self.assertEqual(len(names), len(set(names)), "Duplicate program names found")

    def test_display_names_title_case(self):
        """Display names should be title case."""
        dh = self.registry.diehard_tests()
        for test in dh:
            self.assertEqual(test.display_name, test.display_name.title(),
                             f"Display name not title case: {test.display_name}")

    def test_test_type_is_diehard(self):
        """All Diehard tests should have test_type 'diehard'."""
        for test in self.registry.diehard_tests():
            self.assertEqual(test.test_type, "diehard")


class TestDabEditableParams(unittest.TestCase):
    """Test GUI editable parameter definitions for DAB tests."""

    def setUp(self):
        from main_window import TEST_EDITABLE_PARAMS
        self.params = TEST_EDITABLE_PARAMS

    def test_dab_tests_with_params(self):
        """DAB tests with test-specific params should have definitions."""
        expected_prefixes = [
            "diehard_dab_dct",
            "diehard_dab_filltree",
            "diehard_dab_filltree2",
            "diehard_dab_monobit2",
            # dab_bytedistrib has no test-specific params
        ]
        for prefix in expected_prefixes:
            self.assertIn(prefix, self.params, f"Missing params for {prefix}")

    def test_bytedistrib_no_test_params(self):
        """dab_bytedistrib should NOT have test-specific params."""
        self.assertNotIn("diehard_dab_bytedistrib", self.params,
                         "dab_bytedistrib should not have test-specific params")

    def test_param_defs_have_required_fields(self):
        """Each DAB param def must have label, key, type, default, min, max."""
        required_fields = {"label", "key", "type", "default", "min", "max"}
        dab_prefixes = [k for k in self.params if k.startswith("diehard_dab_")]
        for prefix in dab_prefixes:
            for pdef in self.params[prefix]:
                for field in required_fields:
                    self.assertIn(field, pdef,
                                  f"Missing field '{field}' in {prefix} param '{pdef.get('label', '?')}'")

    def test_dab_dct_params(self):
        """DAB DCT should have block size param."""
        params = self.params["diehard_dab_dct"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "block size")
        self.assertEqual(params[0]["default"], 256)

    def test_dab_filltree_params(self):
        """DAB Fill Tree should have tree depth param."""
        params = self.params["diehard_dab_filltree"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "tree depth")
        self.assertEqual(params[0]["default"], 15)

    def test_dab_filltree2_params(self):
        """DAB Fill Tree 2 should have tree depth param."""
        params = self.params["diehard_dab_filltree2"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "tree depth")
        self.assertEqual(params[0]["default"], 15)

    def test_dab_monobit2_params(self):
        """DAB Monobit 2 should have block size param."""
        params = self.params["diehard_dab_monobit2"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["key"], "block size")
        self.assertEqual(params[0]["default"], 4096)

    def test_default_within_range(self):
        """Default values should be within [min, max]."""
        dab_prefixes = [k for k in self.params if k.startswith("diehard_dab_")]
        for prefix in dab_prefixes:
            for pdef in self.params[prefix]:
                self.assertGreaterEqual(pdef["default"], pdef["min"],
                                        f"Default < min in {prefix}/{pdef['label']}")
                self.assertLessEqual(pdef["default"], pdef["max"],
                                     f"Default > max in {prefix}/{pdef['label']}")


class TestDabPrefixMatching(unittest.TestCase):
    """Test prefix matching for DAB test parameter lookup."""

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

    def test_filltree_no_collision_with_filltree2(self):
        """dab_filltree_test should NOT match dab_filltree2 params."""
        ft_params = self._get_editable_params("diehard_dab_filltree_test")
        ft2_params = self._get_editable_params("diehard_dab_filltree2_test")
        # Both have tree depth, but they should match their own prefix
        self.assertEqual(len(ft_params), 1)
        self.assertEqual(len(ft2_params), 1)

    def test_dab_tests_with_params_match(self):
        """DAB tests with params should find their params."""
        test_names = [
            "diehard_dab_dct_test",
            "diehard_dab_filltree_test",
            "diehard_dab_filltree2_test",
            "diehard_dab_monobit2_test",
        ]
        for name in test_names:
            params = self._get_editable_params(name)
            self.assertTrue(len(params) > 0, f"No params found for {name}")

    def test_bytedistrib_no_match(self):
        """dab_bytedistrib should return empty params."""
        params = self._get_editable_params("diehard_dab_bytedistrib_test")
        self.assertEqual(len(params), 0, "dab_bytedistrib should have no test-specific params")


class TestDabCSourceFiles(unittest.TestCase):
    """Validate structural correctness of DAB C source files."""

    DAB_TESTS = [
        ("dab-bytedistrib", "dab_bytedistrib.c", "diehard_dab_bytedistrib_test"),
        ("dab-dct", "dab_dct.c", "diehard_dab_dct_test"),
        ("dab-filltree", "dab_filltree.c", "diehard_dab_filltree_test"),
        ("dab-filltree2", "dab_filltree2.c", "diehard_dab_filltree2_test"),
        ("dab-monobit2", "dab_monobit2.c", "diehard_dab_monobit2_test"),
    ]

    def test_source_files_exist(self):
        """All 5 DAB C source files should exist."""
        for dirname, filename, _ in self.DAB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            self.assertTrue(path.exists(), f"Missing source file: {path}")

    def test_program_name_correct(self):
        """Each C file should define the correct PROGRAM_NAME."""
        for dirname, filename, expected_name in self.DAB_TESTS:
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
        for dirname, filename, _ in self.DAB_TESTS:
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
        for dirname, filename, _ in self.DAB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            for inc in required_includes:
                self.assertIn(inc, content, f"Missing include '{inc}' in {filename}")

    def test_dieharder_battery_name(self):
        """Each DAB file should reference the Dieharder battery."""
        for dirname, filename, _ in self.DAB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn("Dieharder", content,
                          f"Missing Dieharder reference in {filename}")

    def test_david_bauer_credited(self):
        """Each DAB file should credit David Bauer as author."""
        for dirname, filename, _ in self.DAB_TESTS:
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            self.assertIn("David Bauer", content,
                          f"Missing David Bauer credit in {filename}")

    def test_test_specific_params_in_c(self):
        """DAB C files with test-specific params should parse them."""
        param_checks = {
            "dab_dct.c": "block size",
            "dab_filltree.c": "tree depth",
            "dab_filltree2.c": "tree depth",
            "dab_monobit2.c": "block size",
            # dab_bytedistrib.c has no test-specific params
        }
        for dirname, filename, _ in self.DAB_TESTS:
            if filename not in param_checks:
                continue
            path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / dirname / filename
            if not path.exists():
                self.skipTest(f"File not found: {path}")
            content = path.read_text()
            expected_param = param_checks[filename]
            self.assertIn(f'"{expected_param}"', content,
                          f"Missing parameter '{expected_param}' in {filename}")

    def test_warnings_in_descriptions(self):
        """dab_filltree should include reliability warning."""
        path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / "dab-filltree" / "dab_filltree.c"
        if not path.exists():
            self.skipTest(f"File not found: {path}")
        content = path.read_text()
        # Should contain a warning about reliability
        self.assertTrue(
            "WARNING" in content or "caution" in content.lower() or "unreliable" in content.lower(),
            "dab_filltree.c should contain a reliability warning")

    def test_effectiveness_notes(self):
        """dab_monobit2 should mention effectiveness."""
        path = Path(FRAMEWORK_ROOT) / "src" / "diehard" / "dab-monobit2" / "dab_monobit2.c"
        if not path.exists():
            self.skipTest(f"File not found: {path}")
        content = path.read_text()
        self.assertTrue(
            "most effective" in content.lower() or "most powerful" in content.lower(),
            "dab_monobit2.c should note its effectiveness rating")


class TestDabDocumentation(unittest.TestCase):
    """Test documentation completeness for DAB tests."""

    def setUp(self):
        doc_path = Path(FRAMEWORK_ROOT) / "docs" / "tests" / "test_documentation.json"
        with open(doc_path) as f:
            self.docs = json.load(f)
        self.tests = self.docs["tests"]

    def test_dab_tests_documented(self):
        """All 5 DAB tests should have documentation entries."""
        expected_keys = [
            "dab_bytedistrib",
            "dab_dct",
            "dab_filltree",
            "dab_filltree2",
            "dab_monobit2",
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
        dab_tests = ["dab_bytedistrib", "dab_dct", "dab_filltree",
                     "dab_filltree2", "dab_monobit2"]
        for key in dab_tests:
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            for field in required_fields:
                self.assertIn(field, self.tests[key],
                              f"Missing field '{field}' in docs for '{key}'")

    def test_program_names_match_registry(self):
        """Documentation program_names should match the registry naming convention."""
        expected_mapping = {
            "dab_bytedistrib": "diehard_dab_bytedistrib_test",
            "dab_dct": "diehard_dab_dct_test",
            "dab_filltree": "diehard_dab_filltree_test",
            "dab_filltree2": "diehard_dab_filltree2_test",
            "dab_monobit2": "diehard_dab_monobit2_test",
        }
        for key, expected_prog in expected_mapping.items():
            if key not in self.tests:
                self.skipTest(f"Test '{key}' not in docs")
            self.assertEqual(self.tests[key]["program_name"], expected_prog)

    def test_category_is_dab(self):
        """All DAB tests should be in the Dieharder DAB Tests category."""
        dab_tests = ["dab_bytedistrib", "dab_dct", "dab_filltree",
                     "dab_filltree2", "dab_monobit2"]
        for key in dab_tests:
            if key not in self.tests:
                continue
            self.assertEqual(self.tests[key]["category"], "Dieharder DAB Tests")

    def test_filltree_warning_in_docs(self):
        """dab_filltree documentation should include reliability warning."""
        if "dab_filltree" not in self.tests:
            self.skipTest("dab_filltree not in docs")
        desc = self.tests["dab_filltree"]["description"]
        self.assertTrue(
            "WARNING" in desc or "caution" in desc.lower() or "unreliable" in desc.lower(),
            "dab_filltree docs should contain a reliability warning")

    def test_monobit2_effectiveness_in_docs(self):
        """dab_monobit2 documentation should note its effectiveness rating."""
        if "dab_monobit2" not in self.tests:
            self.skipTest("dab_monobit2 not in docs")
        desc = self.tests["dab_monobit2"]["description"]
        self.assertTrue(
            "most effective" in desc.lower() or "most powerful" in desc.lower(),
            "dab_monobit2 docs should note its effectiveness rating")


class TestDiehardTestNamesFile(unittest.TestCase):
    """Test the diehard_test_names.txt file."""

    def setUp(self):
        path = Path(FRAMEWORK_ROOT) / "build_files" / "diehard_test_names.txt"
        self.names = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    def test_total_count(self):
        """Should have 28 test names."""
        self.assertEqual(len(self.names), 28, f"Expected 28, got {len(self.names)}: {self.names}")

    def test_dab_tests_listed(self):
        """All 5 DAB test names should be in the file."""
        expected = ["dab bytedistrib", "dab dct", "dab filltree",
                    "dab filltree2", "dab monobit2"]
        for name in expected:
            self.assertIn(name, self.names, f"Missing test name: '{name}'")

    def test_no_duplicates(self):
        """No duplicate test names."""
        self.assertEqual(len(self.names), len(set(self.names)),
                         "Duplicate test names found")


if __name__ == "__main__":
    unittest.main(verbosity=2)
