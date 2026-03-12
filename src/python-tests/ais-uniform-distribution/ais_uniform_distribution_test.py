#!/usr/bin/env python3
# =================================================================================================
# ais_uniform_distribution_test.py
# AIS 20/31 Test T6 — Uniform Distribution Test (Procedure B)
#
# Specification: Apply tests T1–T5 to multiple consecutive 20,000-bit
# segments extracted from the bitstream. The test passes only if ALL
# segments pass ALL sub-tests (T1–T5). This is a multi-sample extension
# that verifies the output maintains uniform statistical properties
# across the full length of the generator's output.
#
# Default: 10 segments of 20,000 bits = 200,000 bits minimum.
# =================================================================================================

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SEGMENT_BITS = 20000

# ── T1 Monobit bounds ────────────────────────────────────────────────────────
T1_LOWER = 9654
T1_UPPER = 10346

# ── T2 Poker constants ───────────────────────────────────────────────────────
NIBBLE_SIZE = 4
NUM_NIBBLES = SEGMENT_BITS // NIBBLE_SIZE
NUM_CATEGORIES = 16
T2_LOWER = 1.03
T2_UPPER = 57.4

# ── T3 Runs bounds ───────────────────────────────────────────────────────────
RUN_BOUNDS = {
    1: (2267, 2733),
    2: (1079, 1421),
    3: (502, 748),
    4: (223, 402),
    5: (90, 223),
    6: (90, 223),
}

# ── T4 Long run ──────────────────────────────────────────────────────────────
MAX_RUN_LENGTH = 33

# ── T5 Autocorrelation ───────────────────────────────────────────────────────
HALF_BITS = 5000
MAX_TAU = 5000
T5_LOWER = 2326
T5_UPPER = 2674


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def t1_monobit(segment):
    ones = sum(segment)
    return T1_LOWER <= ones <= T1_UPPER


def t2_poker(segment):
    freq = [0] * NUM_CATEGORIES
    for i in range(NUM_NIBBLES):
        start = i * NIBBLE_SIZE
        val = 0
        for j in range(NIBBLE_SIZE):
            val = (val << 1) | segment[start + j]
        freq[val] += 1
    chi_sq = (NUM_CATEGORIES / NUM_NIBBLES) * sum(f * f for f in freq) - NUM_NIBBLES
    return T2_LOWER <= chi_sq <= T2_UPPER


def t3_runs(segment):
    counts = {0: {i: 0 for i in range(1, 7)},
              1: {i: 0 for i in range(1, 7)}}
    current_bit = segment[0]
    run_length = 1
    for i in range(1, len(segment)):
        if segment[i] == current_bit:
            run_length += 1
        else:
            counts[current_bit][min(run_length, 6)] += 1
            current_bit = segment[i]
            run_length = 1
    counts[current_bit][min(run_length, 6)] += 1
    for bit_val in (0, 1):
        for length, (lo, hi) in RUN_BOUNDS.items():
            if not (lo <= counts[bit_val][length] <= hi):
                return False
    return True


def t4_long_run(segment):
    max_run = 1
    current_bit = segment[0]
    run_length = 1
    for i in range(1, len(segment)):
        if segment[i] == current_bit:
            run_length += 1
        else:
            if run_length > max_run:
                max_run = run_length
            current_bit = segment[i]
            run_length = 1
    if run_length > max_run:
        max_run = run_length
    return max_run <= MAX_RUN_LENGTH


def t5_autocorrelation(segment):
    if len(segment) < HALF_BITS + MAX_TAU:
        return False
    for tau in range(1, MAX_TAU + 1):
        z = sum(segment[i] ^ segment[i + tau] for i in range(HALF_BITS))
        if not (T5_LOWER <= z <= T5_UPPER):
            return False
    return True


SUB_TESTS = [
    ("T1 monobit", t1_monobit),
    ("T2 poker", t2_poker),
    ("T3 runs", t3_runs),
    ("T4 long run", t4_long_run),
    ("T5 autocorrelation", t5_autocorrelation),
]


class AISUniformDistributionTest(SteerTest):
    test_name = "ais uniform distribution"
    program_name = "ais_uniform_distribution_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T6 (Uniform Distribution — Procedure B). Applies "
        "tests T1–T5 to multiple consecutive 20,000-bit segments. All "
        "segments must pass all sub-tests."
    )

    def __init__(self):
        self.bitstream_count = 1
        self.bitstream_length = 1000000
        self.alpha = 0.01
        self.num_segments = 10

    def get_parameters_info(self):
        return [
            {"name": "bitstream count", "data type": "unsigned 64-bit integer",
             "units": "bitstreams", "default": "1", "minimum": "1"},
            {"name": "bitstream length", "data type": "unsigned 64-bit integer",
             "units": "bits", "default": "1000000",
             "minimum": str(SEGMENT_BITS)},
            {"name": "significance level (alpha)",
             "data type": "double precision floating point",
             "precision": "6", "default": "0.01"},
            {"name": "number of segments", "data type": "signed 32-bit integer",
             "default": "10", "minimum": "2"},
        ]

    def init_test(self, params):
        self.bitstream_count = params.get_int("bitstream count")
        self.bitstream_length = params.get_int("bitstream length")
        self.alpha = params.get_float("significance level (alpha)")
        if params.has("number of segments"):
            self.num_segments = params.get_int("number of segments")

    def get_configuration_count(self):
        return 1

    def execute(self, report, bitstream_id, buffer, num_zeros, num_ones):
        bits = buffer_to_bits(buffer)
        total_bits = len(bits)
        actual_segments = min(self.num_segments, total_bits // SEGMENT_BITS)

        segment_results = []
        all_passed = True
        fail_details = []

        for s in range(actual_segments):
            start = s * SEGMENT_BITS
            seg = bits[start:start + SEGMENT_BITS]
            seg_pass = True
            for test_name, test_fn in SUB_TESTS:
                result = test_fn(seg)
                if not result:
                    seg_pass = False
                    fail_details.append(f"segment {s+1}: {test_name} failed")
            segment_results.append(seg_pass)
            if not seg_pass:
                all_passed = False

        passed_count = sum(segment_results)

        calculations = [
            make_calculation("segments tested", str(actual_segments),
                             data_type="signed 32-bit integer"),
            make_calculation("segments passed", str(passed_count),
                             data_type="signed 32-bit integer"),
            make_calculation("segments failed", str(actual_segments - passed_count),
                             data_type="signed 32-bit integer"),
        ]

        criteria = [
            make_criterion(
                f"all {actual_segments} segments pass T1-T5", all_passed
            )
        ]
        for detail in fail_details[:10]:
            criteria.append(make_criterion(detail, False))

        report.add_test_to_configuration(
            1, bitstream_id, calculations=calculations,
            criteria=criteria, evaluation="pass" if all_passed else "fail"
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
    sys.exit(steer_run(AISUniformDistributionTest()))
