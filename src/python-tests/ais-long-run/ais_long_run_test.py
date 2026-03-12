#!/usr/bin/env python3
# =================================================================================================
# ais_long_run_test.py
# AIS 20/31 Test T4 — Long Run Test
#
# Specification: In 20,000 bits, no run of identical bits may have
# length >= 34.
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000
MAX_RUN_LENGTH = 33  # longest allowed run; >= 34 is failure


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def long_run_test(bits):
    """AIS 31 T4: Find the longest run in 20,000 bits.

    Returns (passed, longest_run_length, longest_run_bit).
    """
    sample = bits[:SAMPLE_BITS]
    if not sample:
        return True, 0, -1

    max_run = 1
    max_bit = sample[0]
    current_bit = sample[0]
    run_length = 1

    for i in range(1, len(sample)):
        if sample[i] == current_bit:
            run_length += 1
        else:
            if run_length > max_run:
                max_run = run_length
                max_bit = current_bit
            current_bit = sample[i]
            run_length = 1
    if run_length > max_run:
        max_run = run_length
        max_bit = current_bit

    return max_run <= MAX_RUN_LENGTH, max_run, max_bit


class AISLongRunTest(SteerTest):
    test_name = "ais long run"
    program_name = "ais_long_run_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T4 (Long Run). Scans a 20,000-bit sample for the "
        "longest run of identical bits. No run of length 34 or more is "
        "allowed."
    )

    def __init__(self):
        self.bitstream_count = 1
        self.bitstream_length = 1000000
        self.alpha = 0.01

    def get_parameters_info(self):
        return [
            {"name": "bitstream count", "data type": "unsigned 64-bit integer",
             "units": "bitstreams", "default": "1", "minimum": "1"},
            {"name": "bitstream length", "data type": "unsigned 64-bit integer",
             "units": "bits", "default": "1000000",
             "minimum": str(SAMPLE_BITS)},
            {"name": "significance level (alpha)",
             "data type": "double precision floating point",
             "precision": "6", "default": "0.01"},
        ]

    def init_test(self, params):
        self.bitstream_count = params.get_int("bitstream count")
        self.bitstream_length = params.get_int("bitstream length")
        self.alpha = params.get_float("significance level (alpha)")

    def get_configuration_count(self):
        return 1

    def execute(self, report, bitstream_id, buffer, num_zeros, num_ones):
        bits = buffer_to_bits(buffer)
        sample = bits[:SAMPLE_BITS]

        passed, longest, longest_bit = long_run_test(sample)

        calculations = [
            make_calculation("longest run length", str(longest),
                             data_type="signed 32-bit integer"),
            make_calculation("longest run bit value", str(longest_bit),
                             data_type="signed 32-bit integer"),
            make_calculation("maximum allowed run length",
                             str(MAX_RUN_LENGTH),
                             data_type="signed 32-bit integer"),
        ]

        criteria = [
            make_criterion(
                f"longest run <= {MAX_RUN_LENGTH}", passed
            )
        ]

        report.add_test_to_configuration(
            1, bitstream_id, calculations=calculations,
            criteria=criteria, evaluation="pass" if passed else "fail"
        )

    def finalize(self, report, num_bitstreams):
        config = report.get_configuration(1)
        if config is None:
            return
        all_pass = all(t["evaluation"] == "pass" for t in config["tests"])
        report.add_criterion_to_configuration(1, "All tests passed", all_pass)
        report.set_configuration_evaluation(1, "pass" if all_pass else "fail")
        report.add_report_criterion("All configurations passed", all_pass)
        report.set_evaluation("pass" if all_pass else "fail")


if __name__ == "__main__":
    sys.exit(steer_run(AISLongRunTest()))
