#!/usr/bin/env python3
# =================================================================================================
# ais_runs_test.py
# AIS 20/31 Test T3 — Runs Test
#
# Specification: In 20,000 bits, count runs of consecutive identical bits.
# Runs are categorized by length (1, 2, 3, 4, 5, 6+) and by bit value (0 or 1).
# Each category count must lie within specified bounds.
#
# Bounds per run length (apply to both 0-runs and 1-runs):
#   Length 1:  [2267, 2733]
#   Length 2:  [1079, 1421]
#   Length 3:  [502,  748]
#   Length 4:  [223,  402]
#   Length 5:  [90,   223]
#   Length 6+: [90,   223]
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000

# (lower, upper) bounds for run lengths 1..6+
RUN_BOUNDS = {
    1: (2267, 2733),
    2: (1079, 1421),
    3: (502, 748),
    4: (223, 402),
    5: (90, 223),
    6: (90, 223),   # 6 means "6 or more"
}


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def runs_test(bits):
    """AIS 31 T3: Count runs in 20,000 bits per length and value.

    Returns (all_passed, run_counts_0, run_counts_1, failures).
    run_counts_X is a dict {length: count} for lengths 1..6 (6 = 6+).
    """
    sample = bits[:SAMPLE_BITS]
    # Count runs per bit value and length
    counts = {0: {i: 0 for i in range(1, 7)},
              1: {i: 0 for i in range(1, 7)}}

    if not sample:
        return True, counts[0], counts[1], []

    current_bit = sample[0]
    run_length = 1

    for i in range(1, len(sample)):
        if sample[i] == current_bit:
            run_length += 1
        else:
            # Record the completed run
            key = min(run_length, 6)
            counts[current_bit][key] += 1
            current_bit = sample[i]
            run_length = 1
    # Record final run
    key = min(run_length, 6)
    counts[current_bit][key] += 1

    # Check bounds
    failures = []
    all_passed = True
    for bit_val in (0, 1):
        for length, (lo, hi) in RUN_BOUNDS.items():
            c = counts[bit_val][length]
            if not (lo <= c <= hi):
                all_passed = False
                label = f"{length}+" if length == 6 else str(length)
                failures.append(
                    f"{'ones' if bit_val else 'zeros'} run length {label}: "
                    f"{c} not in [{lo}, {hi}]"
                )

    return all_passed, counts[0], counts[1], failures


class AISRunsTest(SteerTest):
    test_name = "ais runs"
    program_name = "ais_runs_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T3 (Runs). Counts runs of consecutive identical "
        "bits in a 20,000-bit sample, categorized by length (1–5, 6+) "
        "and bit value. Each category must fall within specified bounds."
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

        passed, counts0, counts1, failures = runs_test(sample)

        calculations = []
        for bit_val, counts in [(0, counts0), (1, counts1)]:
            label = "zeros" if bit_val == 0 else "ones"
            for length in range(1, 7):
                length_label = f"{length}+" if length == 6 else str(length)
                lo, hi = RUN_BOUNDS[length]
                calculations.append(
                    make_calculation(
                        f"{label} runs of length {length_label}",
                        str(counts[length]),
                        data_type="signed 32-bit integer"
                    )
                )

        criteria = [
            make_criterion(
                "all run counts within AIS 31 bounds", passed
            )
        ]
        if failures:
            for f in failures[:5]:  # limit to 5 failure details
                criteria.append(make_criterion(f, False))

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
    sys.exit(steer_run(AISRunsTest()))
