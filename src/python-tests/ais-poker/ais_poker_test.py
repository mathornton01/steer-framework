#!/usr/bin/env python3
# =================================================================================================
# ais_poker_test.py
# AIS 20/31 Test T2 — Poker Test
#
# Specification: Divide 20,000 bits into 5,000 non-overlapping 4-bit nibbles.
# Count f(i) = frequency of each nibble value i (0..15).
# Compute X = (16/5000) * sum(f(i)^2) - 5000.
# X must lie within [1.03, 57.4].
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000
NIBBLE_SIZE = 4
NUM_NIBBLES = SAMPLE_BITS // NIBBLE_SIZE  # 5000
NUM_CATEGORIES = 2 ** NIBBLE_SIZE          # 16
LOWER_BOUND = 1.03
UPPER_BOUND = 57.4


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def poker_test(bits):
    """AIS 31 T2: Poker test on 20,000 bits.

    Returns (passed, chi_squared, frequencies).
    """
    sample = bits[:SAMPLE_BITS]
    freq = [0] * NUM_CATEGORIES
    for i in range(NUM_NIBBLES):
        start = i * NIBBLE_SIZE
        val = 0
        for j in range(NIBBLE_SIZE):
            val = (val << 1) | sample[start + j]
        freq[val] += 1

    sum_sq = sum(f * f for f in freq)
    chi_sq = (NUM_CATEGORIES / NUM_NIBBLES) * sum_sq - NUM_NIBBLES

    passed = LOWER_BOUND <= chi_sq <= UPPER_BOUND
    return passed, chi_sq, freq


class AISPokerTest(SteerTest):
    test_name = "ais poker"
    program_name = "ais_poker_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T2 (Poker). Divides 20,000 bits into 5,000 "
        "4-bit nibbles, computes a chi-squared statistic on their "
        "frequency distribution. The statistic must lie within [1.03, 57.4]."
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

        passed, chi_sq, freq = poker_test(sample)

        calculations = [
            make_calculation("chi-squared statistic", f"{chi_sq:.6f}",
                             precision="6"),
            make_calculation("lower bound", f"{LOWER_BOUND:.2f}",
                             precision="2"),
            make_calculation("upper bound", f"{UPPER_BOUND:.1f}",
                             precision="1"),
            make_calculation("number of nibbles", str(NUM_NIBBLES),
                             data_type="signed 32-bit integer"),
        ]

        criteria = [
            make_criterion(
                f"chi-squared in [{LOWER_BOUND}, {UPPER_BOUND}]", passed
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
    sys.exit(steer_run(AISPokerTest()))
