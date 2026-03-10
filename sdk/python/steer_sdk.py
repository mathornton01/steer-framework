#!/usr/bin/env python3
# =================================================================================================
# steer_sdk.py
# Python SDK for STEER Framework test programs
#
# This module provides the scaffolding needed to write STEER-compatible test programs
# in Python. It handles CLI argument parsing, bitstream reading, parameter loading,
# and JSON report generation — matching the contract expected by the STEER test scheduler.
#
# Usage:
#   Subclass SteerTest, implement the required methods, and call steer_run().
#
# Copyright (c) 2024 Anametric, Inc. All rights reserved.
# =================================================================================================

import argparse
import json
import os
import platform
import struct
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone


# =================================================================================================
#  Constants
# =================================================================================================

STEER_RESULT_SUCCESS = 0
STEER_RESULT_FAILURE = -1

REPORT_LEVEL_SUMMARY = "summary"
REPORT_LEVEL_STANDARD = "standard"
REPORT_LEVEL_FULL = "full"


# =================================================================================================
#  SteerParameters — parsed parameter set from JSON
# =================================================================================================

class SteerParameters:
    """Parsed parameter set from a STEER parameters JSON file."""

    def __init__(self, json_data):
        param_set = json_data.get("parameter set", {})
        self.test_name = param_set.get("test name", "")
        self.parameter_set_name = param_set.get("parameter set name", "")
        self._params = {}
        for p in param_set.get("parameters", []):
            self._params[p["name"]] = p

    def get_string(self, name):
        """Get a parameter value as a string."""
        p = self._params.get(name)
        if p is None:
            raise KeyError(f"Parameter '{name}' not found")
        return p["value"]

    def get_int(self, name):
        """Get a parameter value as an integer."""
        return int(self.get_string(name))

    def get_float(self, name):
        """Get a parameter value as a float."""
        return float(self.get_string(name))

    def get(self, name, default=None):
        """Get a parameter value as a string, with a default if not found."""
        p = self._params.get(name)
        if p is None:
            return default
        return p["value"]

    def has(self, name):
        """Check if a parameter exists."""
        return name in self._params

    def raw(self):
        """Return the raw parameter list for report inclusion."""
        return list(self._params.values())


# =================================================================================================
#  SteerReport — builds the JSON report structure
# =================================================================================================

class SteerReport:
    """Builds a STEER-compatible JSON report."""

    def __init__(self, test_name, program_name, program_version, entropy_source,
                 parameters, report_level=REPORT_LEVEL_FULL, conductor=None,
                 notes=None, schedule_id=None):
        self.report = {
            "test name": test_name,
            "program name": program_name,
            "program version": program_version,
            "operating system": platform.system().lower(),
            "architecture": platform.machine(),
            "entropy source": entropy_source,
            "start time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completion time": "",
            "test duration": "",
        }
        if conductor:
            self.report["test conductor"] = conductor
        if notes:
            self.report["test notes"] = notes
        if schedule_id:
            self.report["schedule id"] = schedule_id

        self.report["report level"] = report_level
        self.report["parameters"] = parameters.raw()
        self.report["configurations"] = []
        self.report["criteria"] = []
        self.report["evaluation"] = "inconclusive"

        self._report_level = report_level
        self._start_time = time.time()

    def add_configuration(self, config_id, attributes=None):
        """Add a new configuration to the report. Returns the config dict."""
        config = {
            "configuration id": str(config_id),
            "tests": [],
            "criteria": [],
            "evaluation": "inconclusive",
        }
        if attributes:
            config["attributes"] = attributes
        if self._report_level == REPORT_LEVEL_FULL:
            config["metrics"] = []
        self.report["configurations"].append(config)
        return config

    def get_configuration(self, config_id):
        """Get a configuration by its ID (1-indexed string)."""
        config_id_str = str(config_id)
        for config in self.report["configurations"]:
            if config["configuration id"] == config_id_str:
                return config
        return None

    def add_test_to_configuration(self, config_id, test_id, calculations=None,
                                   criteria=None, evaluation="inconclusive"):
        """Add a test result to a configuration."""
        config = self.get_configuration(config_id)
        if config is None:
            raise ValueError(f"Configuration '{config_id}' not found")

        test_entry = {
            "test id": str(test_id),
            "criteria": criteria or [],
            "evaluation": evaluation,
        }
        if self._report_level == REPORT_LEVEL_FULL and calculations:
            test_entry["calculations"] = calculations
        config["tests"].append(test_entry)
        return test_entry

    def add_metric_to_configuration(self, config_id, name, value, data_type,
                                     precision=None, units=None):
        """Add a metric to a configuration (full report level only)."""
        if self._report_level != REPORT_LEVEL_FULL:
            return
        config = self.get_configuration(config_id)
        if config is None:
            return
        metric = {"name": name, "data type": data_type, "value": str(value)}
        if precision is not None:
            metric["precision"] = str(precision)
        if units is not None:
            metric["units"] = units
        config.setdefault("metrics", []).append(metric)

    def add_criterion_to_configuration(self, config_id, criterion, result):
        """Add a criterion to a configuration."""
        config = self.get_configuration(config_id)
        if config is None:
            return
        config["criteria"].append({"criterion": criterion, "result": result})

    def set_configuration_evaluation(self, config_id, evaluation):
        """Set the evaluation for a configuration."""
        config = self.get_configuration(config_id)
        if config is not None:
            config["evaluation"] = evaluation

    def add_report_criterion(self, criterion, result):
        """Add a top-level criterion to the report."""
        self.report["criteria"].append({"criterion": criterion, "result": result})

    def set_evaluation(self, evaluation):
        """Set the overall report evaluation."""
        self.report["evaluation"] = evaluation

    def finalize(self):
        """Finalize the report with completion time and duration."""
        end_time = time.time()
        duration = end_time - self._start_time
        self.report["completion time"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        self.report["test duration"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def to_json(self):
        """Serialize the report to a JSON string."""
        return json.dumps({"report": self.report}, indent=4)


# =================================================================================================
#  Bitstream reading utilities
# =================================================================================================

def read_bitstream(file_path, offset_bytes, length_bytes):
    """Read a chunk of bytes from an entropy file.

    Args:
        file_path: Path to the binary entropy file.
        offset_bytes: Byte offset to start reading from.
        length_bytes: Number of bytes to read.

    Returns:
        bytes object with the data read, or empty bytes on EOF.
    """
    with open(file_path, "rb") as f:
        f.seek(offset_bytes)
        return f.read(length_bytes)


def count_bits(buffer):
    """Count the number of zero and one bits in a buffer.

    Args:
        buffer: bytes object.

    Returns:
        Tuple of (num_zeros, num_ones).
    """
    num_ones = 0
    for byte in buffer:
        num_ones += bin(byte).count("1")
    total_bits = len(buffer) * 8
    num_zeros = total_bits - num_ones
    return num_zeros, num_ones


# =================================================================================================
#  Calculation/criterion helper builders
# =================================================================================================

def make_calculation(name, value, data_type="double precision floating point",
                     precision=None, units=None):
    """Create a calculation dict for inclusion in a test report.

    Args:
        name: Name of the calculation (e.g., "probability value").
        value: The value (will be converted to string).
        data_type: STEER data type string.
        precision: Optional precision string.
        units: Optional units string.

    Returns:
        Dict conforming to STEER calculation format.
    """
    calc = {"name": name, "data type": data_type, "value": str(value)}
    if precision is not None:
        calc["precision"] = str(precision)
    if units is not None:
        calc["units"] = units
    return calc


def make_criterion(criterion_text, result):
    """Create a criterion dict.

    Args:
        criterion_text: Description of the criterion.
        result: Boolean pass/fail.

    Returns:
        Dict conforming to STEER criterion format.
    """
    return {"criterion": criterion_text, "result": bool(result)}


# =================================================================================================
#  SteerTest — abstract base class for Python STEER tests
# =================================================================================================

class SteerTest(ABC):
    """Abstract base class for STEER test programs written in Python.

    Subclasses must implement:
        - test_name:        class attribute or property
        - program_name:     class attribute or property
        - program_version:  class attribute or property
        - get_parameters_info(): returns parameter schema list
        - init_test(params): initialize with parsed parameters
        - get_configuration_count(): return number of configurations
        - execute(report, bitstream_id, buffer, num_zeros, num_ones): run test on one bitstream
        - finalize(report, num_bitstreams): finalize results
    """

    # Subclasses should set these
    test_name = "unnamed test"
    program_name = "unnamed_program"
    program_version = "0.1.0"
    test_description = ""

    @abstractmethod
    def get_parameters_info(self):
        """Return a list of parameter info dicts describing accepted parameters.

        Each dict should have: name, data_type, units (optional),
        default (optional), minimum (optional), maximum (optional).
        """
        pass

    @abstractmethod
    def init_test(self, params):
        """Initialize the test with parsed parameters.

        Args:
            params: SteerParameters instance.

        Should store bitstream_count, bitstream_length, and any test-specific
        parameters as instance attributes.
        """
        pass

    @abstractmethod
    def get_configuration_count(self):
        """Return the number of test configurations (usually 1)."""
        pass

    @abstractmethod
    def execute(self, report, bitstream_id, buffer, num_zeros, num_ones):
        """Execute the test on a single bitstream.

        Args:
            report: SteerReport instance to populate.
            bitstream_id: 1-indexed bitstream identifier (string).
            buffer: bytes object containing the bitstream data.
            num_zeros: Count of zero bits in buffer.
            num_ones: Count of one bits in buffer.
        """
        pass

    @abstractmethod
    def finalize(self, report, num_bitstreams):
        """Finalize the test after all bitstreams have been processed.

        Args:
            report: SteerReport instance to finalize.
            num_bitstreams: Total number of bitstreams processed.
        """
        pass


# =================================================================================================
#  steer_run — main entry point for Python STEER tests
# =================================================================================================

def steer_run(test):
    """Run a STEER test program.

    This function handles CLI argument parsing, bitstream reading, report creation,
    and output — matching the behavior of the C STEER_Run() function.

    Args:
        test: An instance of a SteerTest subclass.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        prog=test.program_name,
        description=f"STEER test: {test.test_name}",
    )
    parser.add_argument("-l", "--report-level", default="full",
                        choices=["summary", "standard", "full"],
                        help="Report detail level")
    parser.add_argument("-e", "--entropy-file-path", required=False,
                        help="Path to entropy source file")
    parser.add_argument("-p", "--parameters-file-path", required=False,
                        help="Path to parameters JSON file")
    parser.add_argument("-P", "--parameters", required=False,
                        help="Inline parameters JSON string")
    parser.add_argument("-r", "--report-file-path", required=False,
                        help="Path for output report JSON file")
    parser.add_argument("-c", "--conductor", required=False,
                        help="Test conductor name")
    parser.add_argument("-n", "--notes", required=False,
                        help="Test notes")
    parser.add_argument("-s", "--schedule-id", required=False,
                        help="Schedule ID")
    parser.add_argument("-R", "--report-progress", action="store_true",
                        help="Report progress to stdout")
    parser.add_argument("-t", "--test-info", action="store_true",
                        help="Print test info and exit")
    parser.add_argument("-i", "--parameters-info", action="store_true",
                        help="Print parameters info and exit")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("-V", "--version", action="store_true",
                        help="Print version and exit")

    args = parser.parse_args()

    # Handle info/version commands
    if args.version:
        print(f"{test.program_name} {test.program_version}")
        return STEER_RESULT_SUCCESS

    if args.test_info:
        info = {
            "test info": {
                "test name": test.test_name,
                "test description": test.test_description,
                "program name": test.program_name,
                "program version": test.program_version,
            }
        }
        print(json.dumps(info, indent=4))
        return STEER_RESULT_SUCCESS

    if args.parameters_info:
        info = {"parameters info": test.get_parameters_info()}
        print(json.dumps(info, indent=4))
        return STEER_RESULT_SUCCESS

    # Validate required arguments for test execution
    if not args.entropy_file_path:
        print("Error: --entropy-file-path is required for test execution",
              file=sys.stderr)
        return STEER_RESULT_FAILURE

    # Load parameters
    params_json = None
    if args.parameters_file_path:
        with open(args.parameters_file_path, "r") as f:
            params_json = json.load(f)
    elif args.parameters:
        params_json = json.loads(args.parameters)
    else:
        print("Error: parameters must be provided via -p or -P", file=sys.stderr)
        return STEER_RESULT_FAILURE

    params = SteerParameters(params_json)

    # Initialize the test
    test.init_test(params)

    bitstream_count = params.get_int("bitstream count")
    bitstream_length = params.get_int("bitstream length")
    buffer_size = bitstream_length // 8

    # Create the report
    report = SteerReport(
        test_name=test.test_name,
        program_name=test.program_name,
        program_version=test.program_version,
        entropy_source=args.entropy_file_path,
        parameters=params,
        report_level=args.report_level,
        conductor=args.conductor,
        notes=args.notes,
        schedule_id=args.schedule_id,
    )

    # Set up configurations
    config_count = test.get_configuration_count()
    for i in range(1, config_count + 1):
        report.add_configuration(i)

    # Process bitstreams
    for i in range(bitstream_count):
        bitstream_id = str(i + 1)
        offset = i * buffer_size
        buffer = read_bitstream(args.entropy_file_path, offset, buffer_size)

        if len(buffer) < buffer_size:
            if args.verbose:
                print(f"Warning: short read at bitstream {bitstream_id}",
                      file=sys.stderr)
            break

        num_zeros, num_ones = count_bits(buffer)

        if args.report_progress:
            print(f"Executing test with bitstream {bitstream_id}...")

        test.execute(report, bitstream_id, buffer, num_zeros, num_ones)

    # Finalize
    test.finalize(report, bitstream_count)
    report.finalize()

    # Write report
    report_json = report.to_json()
    if args.report_file_path:
        report_dir = os.path.dirname(args.report_file_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(args.report_file_path, "w") as f:
            f.write(report_json)
    else:
        print(report_json)

    return STEER_RESULT_SUCCESS


# =================================================================================================
#  Main (for testing the SDK itself)
# =================================================================================================

if __name__ == "__main__":
    print("STEER Python SDK loaded successfully.")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.machine()}")
