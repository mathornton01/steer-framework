#!/usr/bin/env python3
# =================================================================================================
# ais_homogeneity_test.py
# AIS 20/31 Test T7 — Homogeneity Test (Procedure B)
#
# Specification: Tests that different segments of the RNG output have
# statistically identical properties. Splits the bitstream into Q
# non-overlapping segments, computes the monobit proportion in each,
# and applies a chi-squared homogeneity test to determine whether
# all segments come from the same distribution.
#
# The null hypothesis is that all segments have the same proportion of
# ones (p = 0.5 for an ideal RNG). The chi-squared statistic with
# Q-1 degrees of freedom tests whether the observed variation across
# segments exceeds what is expected by chance.
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


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def chi2_cdf(x, k):
    """Approximate chi-squared CDF using the regularized incomplete gamma function.

    Uses the series expansion of the lower incomplete gamma function.
    """
    if x <= 0:
        return 0.0
    half_k = k / 2.0
    half_x = x / 2.0
    # Use series expansion: P(a, x) = e^{-x} x^a sum_{n=0}^{inf} x^n / Gamma(a+n+1)
    # which equals gamma(a, x) / Gamma(a)
    # Regularized lower incomplete gamma via series
    s = 1.0 / half_k
    term = 1.0 / half_k
    for n in range(1, 300):
        term *= half_x / (half_k + n)
        s += term
        if abs(term) < 1e-15:
            break
    try:
        p = s * math.exp(-half_x + half_k * math.log(half_x) - math.lgamma(half_k))
    except (ValueError, OverflowError):
        p = 1.0 if x > k else 0.0
    return min(max(p, 0.0), 1.0)


def homogeneity_test(bits, num_segments, alpha=0.01):
    """AIS 31 T7: Chi-squared homogeneity test across segments.

    Splits bitstream into num_segments of SEGMENT_BITS each.
    Counts ones per segment, runs chi-squared test of homogeneity.

    Returns (passed, chi_sq, p_value, segment_ones, df).
    """
    total_needed = num_segments * SEGMENT_BITS
    actual_segments = min(num_segments, len(bits) // SEGMENT_BITS)
    if actual_segments < 2:
        return True, 0.0, 1.0, [], 0

    segment_ones = []
    for s in range(actual_segments):
        start = s * SEGMENT_BITS
        ones = sum(bits[start:start + SEGMENT_BITS])
        segment_ones.append(ones)

    # Overall proportion
    total_ones = sum(segment_ones)
    total_n = actual_segments * SEGMENT_BITS
    p_hat = total_ones / total_n  # pooled proportion

    # Chi-squared statistic
    chi_sq = 0.0
    for ones in segment_ones:
        zeros = SEGMENT_BITS - ones
        e_ones = SEGMENT_BITS * p_hat
        e_zeros = SEGMENT_BITS * (1.0 - p_hat)
        if e_ones > 0:
            chi_sq += (ones - e_ones) ** 2 / e_ones
        if e_zeros > 0:
            chi_sq += (zeros - e_zeros) ** 2 / e_zeros

    df = actual_segments - 1
    p_value = 1.0 - chi2_cdf(chi_sq, df) if df > 0 else 1.0
    passed = p_value >= alpha

    return passed, chi_sq, p_value, segment_ones, df


class AISHomogeneityTest(SteerTest):
    test_name = "ais homogeneity"
    program_name = "ais_homogeneity_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T7 (Homogeneity — Procedure B). Splits the "
        "bitstream into multiple 20,000-bit segments and applies a "
        "chi-squared homogeneity test to verify all segments have "
        "statistically identical proportions of ones."
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
             "minimum": str(SEGMENT_BITS * 2)},
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

        passed, chi_sq, p_value, seg_ones, df = homogeneity_test(
            bits, self.num_segments, self.alpha
        )

        actual_segs = len(seg_ones)
        calculations = [
            make_calculation("chi-squared statistic", f"{chi_sq:.6f}",
                             precision="6"),
            make_calculation("probability value", f"{p_value:.6f}",
                             precision="6"),
            make_calculation("degrees of freedom", str(df),
                             data_type="signed 32-bit integer"),
            make_calculation("segments tested", str(actual_segs),
                             data_type="signed 32-bit integer"),
        ]
        if seg_ones:
            min_ones = min(seg_ones)
            max_ones = max(seg_ones)
            calculations.append(
                make_calculation("min segment ones", str(min_ones),
                                 data_type="signed 32-bit integer")
            )
            calculations.append(
                make_calculation("max segment ones", str(max_ones),
                                 data_type="signed 32-bit integer")
            )

        criteria = [
            make_criterion(
                f"probability value >= {self.alpha:.6f} (significance level)",
                passed
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
    sys.exit(steer_run(AISHomogeneityTest()))
