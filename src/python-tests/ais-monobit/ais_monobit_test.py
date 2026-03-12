#!/usr/bin/env python3
# =================================================================================================
# ais_monobit_test.py
# AIS 20/31 Test T1 — Monobit Test
#
# Specification: In a 20,000-bit sample, the number of ones must lie within
# [9654, 10346].
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000
LOWER_BOUND = 9654
UPPER_BOUND = 10346


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def monobit_test(bits):
    """AIS 31 T1: Count ones in 20,000 bits. Must be in [9654, 10346].

    Returns (passed, ones_count).
    """
    ones = sum(bits[:SAMPLE_BITS])
    return LOWER_BOUND <= ones <= UPPER_BOUND, ones


class AISMonobitTest(SteerTest):
    test_name = "ais monobit"
    program_name = "ais_monobit_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T1 (Monobit). Counts the number of ones in a "
        "20,000-bit sample. The count must lie within [9654, 10346]."
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

        passed, ones_count = monobit_test(sample)

        calculations = [
            make_calculation("ones count", str(ones_count),
                             data_type="signed 32-bit integer"),
            make_calculation("zeros count", str(SAMPLE_BITS - ones_count),
                             data_type="signed 32-bit integer"),
            make_calculation("lower bound", str(LOWER_BOUND),
                             data_type="signed 32-bit integer"),
            make_calculation("upper bound", str(UPPER_BOUND),
                             data_type="signed 32-bit integer"),
        ]

        criteria = [
            make_criterion(
                f"ones count in [{LOWER_BOUND}, {UPPER_BOUND}]", passed
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
    sys.exit(steer_run(AISMonobitTest()))
