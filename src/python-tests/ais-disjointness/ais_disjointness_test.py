#!/usr/bin/env python3
# =================================================================================================
# ais_disjointness_test.py
# AIS 20/31 Test T0 — Disjointness Test
#
# Specification: Consecutive non-overlapping 48-bit words must all differ.
# The test takes 20,000 bits, splits into consecutive 48-bit words, and
# verifies that no two adjacent words are identical.
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000
WORD_SIZE = 48


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def disjointness_test(bits):
    """AIS 31 T0: Check that no two consecutive 48-bit words are identical.

    Returns (passed, num_words, num_duplicates, first_dup_index).
    """
    n = len(bits)
    num_words = n // WORD_SIZE
    if num_words < 2:
        return True, num_words, 0, -1

    prev = tuple(bits[0:WORD_SIZE])
    num_duplicates = 0
    first_dup_index = -1
    for i in range(1, num_words):
        start = i * WORD_SIZE
        word = tuple(bits[start:start + WORD_SIZE])
        if word == prev:
            num_duplicates += 1
            if first_dup_index < 0:
                first_dup_index = i
        prev = word

    return num_duplicates == 0, num_words, num_duplicates, first_dup_index


class AISDisjointnessTest(SteerTest):
    test_name = "ais disjointness"
    program_name = "ais_disjointness_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T0 (Disjointness). Verifies that consecutive "
        "non-overlapping 48-bit words within a 20,000-bit sample are all "
        "distinct. Any identical adjacent pair causes a failure."
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
        # Use only the first SAMPLE_BITS
        sample = bits[:SAMPLE_BITS]

        passed, num_words, num_duplicates, first_dup = disjointness_test(sample)

        calculations = [
            make_calculation("number of 48-bit words", str(num_words),
                             data_type="signed 32-bit integer"),
            make_calculation("duplicate adjacent pairs", str(num_duplicates),
                             data_type="signed 32-bit integer"),
        ]
        if first_dup >= 0:
            calculations.append(
                make_calculation("first duplicate at word index", str(first_dup),
                                 data_type="signed 32-bit integer")
            )

        criteria = [
            make_criterion("no two consecutive 48-bit words are identical", passed)
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
    sys.exit(steer_run(AISDisjointnessTest()))
