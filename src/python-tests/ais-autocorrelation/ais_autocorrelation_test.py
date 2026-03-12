#!/usr/bin/env python3
# =================================================================================================
# ais_autocorrelation_test.py
# AIS 20/31 Test T5 — Autocorrelation Test
#
# Specification: For shifts tau = 1..5000, take the first 10,000 bits and
# compute Z(tau) = sum_{i=0}^{4999} XOR(bit[i], bit[i+tau]).
# Each Z(tau) must lie within [2326, 2674].
# =================================================================================================

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)

SAMPLE_BITS = 20000   # need at least 10000 + 5000 = 15000, but AIS spec uses 20000
HALF_BITS = 5000      # correlation window
MAX_TAU = 5000
LOWER_BOUND = 2326
UPPER_BOUND = 2674


def buffer_to_bits(buffer):
    bits = []
    for byte in buffer:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def autocorrelation_test(bits):
    """AIS 31 T5: Autocorrelation test on first 10,000 bits for shifts 1..5000.

    Returns (all_passed, num_failures, first_fail_tau, first_fail_z).
    """
    # Use bits[0..9999] for the correlation; need bits up to index 9999+5000=14999
    n = min(len(bits), SAMPLE_BITS)
    if n < HALF_BITS + MAX_TAU:
        return False, -1, -1, -1

    num_failures = 0
    first_fail_tau = -1
    first_fail_z = -1

    for tau in range(1, MAX_TAU + 1):
        z = 0
        for i in range(HALF_BITS):
            z += bits[i] ^ bits[i + tau]
        if not (LOWER_BOUND <= z <= UPPER_BOUND):
            num_failures += 1
            if first_fail_tau < 0:
                first_fail_tau = tau
                first_fail_z = z

    return num_failures == 0, num_failures, first_fail_tau, first_fail_z


class AISAutocorrelationTest(SteerTest):
    test_name = "ais autocorrelation"
    program_name = "ais_autocorrelation_test"
    program_version = "1.0.0"
    test_description = (
        "AIS 20/31 Test T5 (Autocorrelation). For each shift tau from 1 "
        "to 5000, computes Z(tau) = number of XOR differences between "
        "bit[i] and bit[i+tau] for i=0..4999. Each Z(tau) must lie "
        "within [2326, 2674]."
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

        passed, num_failures, fail_tau, fail_z = autocorrelation_test(bits)

        calculations = [
            make_calculation("shifts tested", str(MAX_TAU),
                             data_type="signed 32-bit integer"),
            make_calculation("failing shifts", str(num_failures),
                             data_type="signed 32-bit integer"),
            make_calculation("lower bound", str(LOWER_BOUND),
                             data_type="signed 32-bit integer"),
            make_calculation("upper bound", str(UPPER_BOUND),
                             data_type="signed 32-bit integer"),
        ]
        if fail_tau >= 0:
            calculations.append(
                make_calculation("first failing shift (tau)", str(fail_tau),
                                 data_type="signed 32-bit integer")
            )
            calculations.append(
                make_calculation("Z at first failing shift", str(fail_z),
                                 data_type="signed 32-bit integer")
            )

        criteria = [
            make_criterion(
                f"all Z(tau) in [{LOWER_BOUND}, {UPPER_BOUND}] for tau=1..{MAX_TAU}",
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
    sys.exit(steer_run(AISAutocorrelationTest()))
