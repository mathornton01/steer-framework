#!/usr/bin/env python3
# =================================================================================================
# steer_docs.py — CLI documentation viewer for STEER Framework tests
# =================================================================================================

import json
import sys
import textwrap
from pathlib import Path


def find_docs_file() -> Path:
    """Locate the test_documentation.json file."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "docs" / "tests" / "test_documentation.json",
        Path(__file__).resolve().parent / "test_documentation.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path("")


def load_docs() -> dict:
    path = find_docs_file()
    if not path.exists():
        print("Error: Could not find test_documentation.json")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def wrap(text: str, width: int = 80, indent: str = "") -> str:
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if line.strip() == "":
            wrapped.append("")
        else:
            wrapped.extend(textwrap.wrap(line, width=width, initial_indent=indent,
                                         subsequent_indent=indent))
    return "\n".join(wrapped)


def print_separator(char: str = "=", width: int = 80):
    print(char * width)


def print_header(text: str, char: str = "="):
    print_separator(char)
    print(f"  {text}")
    print_separator(char)


def list_tests(docs: dict):
    """Print a list of all available tests."""
    tests = docs.get("tests", {})
    print_header("STEER Framework — Available Tests")
    print()

    # Group by category
    categories: dict[str, list] = {}
    for key, test in tests.items():
        cat = test.get("category", "Other")
        categories.setdefault(cat, []).append((key, test))

    for cat, items in categories.items():
        print(f"  {cat}")
        print(f"  {'-' * len(cat)}")
        for key, test in items:
            print(f"    {key:<40s} {test['name']}")
        print()

    print(f"  Total: {len(tests)} tests")
    print()
    print("  Usage: steer_docs.py <test-key>         Show full documentation")
    print("         steer_docs.py <test-key> --brief  Show summary only")
    print("         steer_docs.py --list              List all tests")
    print("         steer_docs.py --search <keyword>  Search documentation")
    print()


def show_test(docs: dict, test_key: str, brief: bool = False):
    """Display documentation for a specific test."""
    tests = docs.get("tests", {})
    test = tests.get(test_key)

    if not test:
        # Try fuzzy match
        matches = [k for k in tests if test_key.lower() in k.lower()
                   or test_key.lower() in tests[k]["name"].lower()]
        if len(matches) == 1:
            test_key = matches[0]
            test = tests[test_key]
        elif matches:
            print(f"Multiple matches for '{test_key}':")
            for m in matches:
                print(f"  {m:<40s} {tests[m]['name']}")
            return
        else:
            print(f"Unknown test: '{test_key}'")
            print("Use --list to see available tests.")
            return

    print_header(test["name"])
    print()

    # Summary
    print("  SUMMARY")
    print("  " + "-" * 7)
    print(wrap(test["summary"], indent="  "))
    print()

    if brief:
        print(f"  Category:  {test['category']}")
        print(f"  Reference: {test['nist_reference']}")
        print(f"  Program:   {test['program_name']}")
        return

    # Metadata
    print("  METADATA")
    print("  " + "-" * 8)
    print(f"  Category:      {test['category']}")
    print(f"  Reference:     {test['nist_reference']}")
    print(f"  Program Name:  {test['program_name']}")
    print()

    # Description
    print("  DESCRIPTION")
    print("  " + "-" * 11)
    print(wrap(test["description"], indent="  "))
    print()

    # Mathematical Basis
    if test.get("mathematical_basis"):
        print("  MATHEMATICAL BASIS")
        print("  " + "-" * 18)
        print(wrap(test["mathematical_basis"], indent="  "))
        print()

    # Parameters
    if test.get("parameters"):
        print("  PARAMETERS")
        print("  " + "-" * 10)
        for pname, pdesc in test["parameters"].items():
            print(f"    {pname}")
            print(wrap(pdesc, indent="      "))
        print()

    # Interpretation
    if test.get("interpretation"):
        print("  INTERPRETATION")
        print("  " + "-" * 14)
        interp = test["interpretation"]
        print(f"    PASS: {interp.get('pass', '')}")
        print(f"    FAIL: {interp.get('fail', '')}")
        print()

    # Recommendations
    if test.get("recommendations"):
        print("  RECOMMENDATIONS")
        print("  " + "-" * 15)
        print(wrap(test["recommendations"], indent="  "))
        print()

    # Example Applications
    if test.get("example_applications"):
        print("  EXAMPLE APPLICATIONS")
        print("  " + "-" * 20)
        for app in test["example_applications"]:
            print(f"    - {app}")
        print()


def search_docs(docs: dict, keyword: str):
    """Search through documentation for a keyword."""
    tests = docs.get("tests", {})
    keyword_lower = keyword.lower()
    results = []

    for key, test in tests.items():
        # Search in all string fields
        searchable = json.dumps(test).lower()
        if keyword_lower in searchable:
            results.append((key, test))

    if not results:
        print(f"No results found for '{keyword}'.")
        return

    print_header(f"Search Results for '{keyword}'")
    print()
    for key, test in results:
        print(f"  {key:<40s} {test['name']}")
        print(wrap(test["summary"], indent="    "))
        print()
    print(f"  {len(results)} result(s) found.")
    print()


def main():
    docs = load_docs()

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print()
        print("  STEER Framework Documentation Viewer")
        print("  " + "=" * 38)
        print()
        print("  Usage:")
        print("    steer_docs.py --list              List all tests")
        print("    steer_docs.py <test-key>           Show full documentation")
        print("    steer_docs.py <test-key> --brief   Show summary only")
        print("    steer_docs.py --search <keyword>   Search documentation")
        print("    steer_docs.py --all                Show all documentation")
        print()
        print("  Examples:")
        print("    steer_docs.py frequency")
        print("    steer_docs.py pearl_causal_model")
        print("    steer_docs.py --search entropy")
        print("    steer_docs.py rank --brief")
        print()
        return

    if sys.argv[1] == "--list":
        list_tests(docs)
    elif sys.argv[1] == "--search":
        if len(sys.argv) < 3:
            print("Usage: steer_docs.py --search <keyword>")
            return
        search_docs(docs, " ".join(sys.argv[2:]))
    elif sys.argv[1] == "--all":
        brief = "--brief" in sys.argv
        tests = docs.get("tests", {})
        for key in tests:
            show_test(docs, key, brief=brief)
            print()
    else:
        test_key = sys.argv[1]
        brief = "--brief" in sys.argv
        show_test(docs, test_key, brief=brief)


if __name__ == "__main__":
    main()
