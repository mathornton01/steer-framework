#!/usr/bin/env python3
# =================================================================================================
# rubin_causal_model_test.py
# STEER wrapper for the Rubin Causal Model MVL Randomness Test
#
# This module adapts the Rubin MVL test to run as a STEER-compatible test program.
# It reads binary entropy data via the STEER CLI contract, runs the Rubin test,
# and outputs a conforming JSON report.
# =================================================================================================

import sys
import os
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import scipy.stats as stats
from collections import defaultdict

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)


# =================================================================================================
#  Rubin MVL core functions (extracted from RCM_MVL_v18.py)
# =================================================================================================

def split_sequence(sequence, subseqsize):
    """Split a sequence into non-overlapping blocks of subseqsize."""
    return [sequence[i:i + subseqsize]
            for i in range(0, len(sequence) - subseqsize + 1, subseqsize)]


def binary_to_nary(bits, base):
    """Convert a list of binary bits into base-k symbols."""
    if base <= 1:
        return bits[:]
    bits_per_symbol = max(1, math.ceil(math.log2(base)))
    result = []
    for i in range(0, len(bits) - bits_per_symbol + 1, bits_per_symbol):
        val = 0
        for j in range(bits_per_symbol):
            val = (val << 1) | bits[i + j]
        result.append(val % base)
    return result


def prepare_dataframe(subsequences, subseqsize, treatpos, outpos):
    """Build a DataFrame from subsequences, extract covariates, one-hot encode."""
    df = pd.DataFrame(subsequences, columns=[str(i) for i in range(subseqsize)])

    # Treatment label = tuple of treatment positions
    treat_cols = [str(p) for p in treatpos]
    out_cols = [str(p) for p in outpos]
    cov_cols = [c for c in df.columns if c not in treat_cols and c not in out_cols]

    # Create treatment labels
    y = df[treat_cols].apply(lambda row: tuple(row), axis=1)

    # One-hot encode covariates
    if cov_cols:
        X = pd.get_dummies(df[cov_cols].astype(str), drop_first=False)
    else:
        X = pd.DataFrame(np.ones((len(df), 1)), columns=["intercept"])

    classes = sorted(y.unique(), key=str)
    return df, X, y, classes


def compute_propensity_scores(X, y, max_samples=10000):
    """Fit multinomial logistic regression to estimate propensity scores."""
    import warnings
    X_arr = X.values.astype(float)
    y_arr = y.values

    # Subsample if too large
    if len(X_arr) > max_samples:
        idx = np.random.choice(len(X_arr), max_samples, replace=False)
        X_fit, y_fit = X_arr[idx], y_arr[idx]
    else:
        X_fit, y_fit = X_arr, y_arr

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = LogisticRegression(
                multi_class="multinomial", solver="lbfgs",
                max_iter=1000, C=1.0
            )
            model.fit(X_fit, y_fit)
        pscores = model.predict_proba(X_arr)
    except Exception:
        # Fallback: uniform propensity scores
        n_classes = len(set(y_arr))
        pscores = np.full((len(X_arr), n_classes), 1.0 / n_classes)

    return pscores


def match_pairs(X, y, pscores, classes):
    """Greedy nearest-neighbor matching: each treatment unit to closest control."""
    y_arr = np.array([str(v) for v in y])
    class_strs = [str(c) for c in classes]

    # Control = most common class
    counts = {c: np.sum(y_arr == c) for c in class_strs}
    control_class = max(counts, key=counts.get)
    control_id = class_strs.index(control_class)

    control_idx = np.where(y_arr == control_class)[0]
    treat_idx = np.where(y_arr != control_class)[0]

    pairs = []
    used = set()
    for ti in treat_idx:
        best_dist = float("inf")
        best_ci = None
        for ci in control_idx:
            if ci in used:
                continue
            dist = np.sum((pscores[ti] - pscores[ci]) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_ci = ci
        if best_ci is not None:
            pairs.append((ti, best_ci))
            used.add(best_ci)

    return pairs, control_id


def hamming_distance_mvl(a, b):
    """Count position-wise mismatches between two lists."""
    return sum(1 for x, y in zip(a, b) if x != y)


def treatment_outcome_pos_validation(subseqsize, treatpos, outpos):
    """Validate that treatment and outcome positions are within bounds and disjoint."""
    all_pos = treatpos + outpos
    if max(all_pos) >= subseqsize or min(all_pos) < 0:
        raise ValueError(
            f"Positions out of bounds: max={max(all_pos)}, subseqsize={subseqsize}"
        )
    if len(set(all_pos)) != len(all_pos):
        raise ValueError("Treatment and outcome positions must be disjoint")


def rubin_randomness_test(sequence, subseqsize, treatpos, outpos,
                          alphabet_size=None, alpha=0.05):
    """Run the Rubin MVL randomness test on a k-ary sequence.

    Returns a dict with distances, z-score, p-value, and interpretation.
    """
    treatment_outcome_pos_validation(subseqsize, treatpos, outpos)

    subsequences = split_sequence(sequence, subseqsize)
    if not subsequences:
        return {"distances": [], "z_score": float("nan"), "p_value": float("nan"),
                "avg_distance": float("nan"), "n_pairs": 0,
                "num_outcome_bits": len(outpos)}

    df, X, y, classes = prepare_dataframe(subsequences, subseqsize, treatpos, outpos)
    pscores = compute_propensity_scores(X, y)
    pairs, control_id = match_pairs(X, y, pscores, classes)

    distances = []
    for ti, ci in pairs:
        out_t = df.iloc[ti, outpos].values.tolist()
        out_c = df.iloc[ci, outpos].values.tolist()
        hd = hamming_distance_mvl(out_t, out_c)
        distances.append(hd)

    m = len(outpos)
    n = len(distances)
    avg_all = np.mean(distances) if n > 0 else np.nan
    prop = (avg_all / m) if (m > 0 and n > 0) else np.nan

    # Null mismatch probability
    if alphabet_size is None:
        symbols = set()
        for pos in outpos:
            symbols.update(df.iloc[:, pos].astype(str).unique().tolist())
        k = max(2, len(symbols))
    else:
        k = int(alphabet_size)
    p0 = 1.0 - 1.0 / float(k)

    se = math.sqrt((p0 * (1 - p0)) / (m * n)) if (n > 0 and m > 0) else np.nan
    z = (prop - p0) / se if (not np.isnan(se) and se > 0) else np.nan
    p_value = 2 * (1 - stats.norm.cdf(abs(z))) if not np.isnan(z) else np.nan

    interp = "Random" if np.isnan(p_value) else (
        "Non-random" if p_value < alpha else "Random"
    )

    return {
        "distances": distances,
        "z_score": float(z) if not np.isnan(z) else None,
        "p_value": float(p_value) if not np.isnan(p_value) else None,
        "avg_distance": float(avg_all) if not np.isnan(avg_all) else None,
        "n_pairs": n,
        "num_outcome_bits": m,
        "null_p_mismatch": p0,
        "interpretation": interp,
    }


# =================================================================================================
#  STEER Test Implementation
# =================================================================================================

class RubinCausalModelTest(SteerTest):
    test_name = "rubin causal model"
    program_name = "rubin_causal_model_test"
    program_version = "1.0.0"
    test_description = (
        "Rubin Causal Model MVL Randomness Test. Uses propensity score matching "
        "and Hamming distance between treatment-control outcome pairs to detect "
        "non-randomness."
    )

    def __init__(self):
        self.bitstream_count = 1
        self.bitstream_length = 1000000
        self.alpha = 0.01
        self.alphabet_size = 3
        self.subseqsize = 6
        self.treatpos = [0, 1]
        self.outpos = [2, 3, 4, 5]

    def get_parameters_info(self):
        return [
            {"name": "bitstream count", "data type": "unsigned 64-bit integer",
             "units": "bitstreams", "default": "1", "minimum": "1"},
            {"name": "bitstream length", "data type": "unsigned 64-bit integer",
             "units": "bits", "default": "1000000", "minimum": "1024"},
            {"name": "significance level (alpha)",
             "data type": "double precision floating point",
             "precision": "6", "default": "0.01"},
            {"name": "alphabet size", "data type": "signed 32-bit integer",
             "default": "3", "minimum": "2"},
            {"name": "subsequence size", "data type": "signed 32-bit integer",
             "default": "6", "minimum": "3"},
            {"name": "treatment positions", "data type": "utf-8 string",
             "default": "0,1"},
            {"name": "outcome positions", "data type": "utf-8 string",
             "default": "2,3,4,5"},
        ]

    def init_test(self, params):
        self.bitstream_count = params.get_int("bitstream count")
        self.bitstream_length = params.get_int("bitstream length")
        self.alpha = params.get_float("significance level (alpha)")

        if params.has("alphabet size"):
            self.alphabet_size = params.get_int("alphabet size")
        if params.has("subsequence size"):
            self.subseqsize = params.get_int("subsequence size")
        if params.has("treatment positions"):
            self.treatpos = [int(x) for x in params.get_string("treatment positions").split(",")]
        if params.has("outcome positions"):
            self.outpos = [int(x) for x in params.get_string("outcome positions").split(",")]

    def get_configuration_count(self):
        return 1

    def execute(self, report, bitstream_id, buffer, num_zeros, num_ones):
        # Convert binary buffer to k-ary sequence
        bits = []
        for byte in buffer:
            for bit_pos in range(7, -1, -1):
                bits.append((byte >> bit_pos) & 1)

        sequence = binary_to_nary(bits, self.alphabet_size)

        # Run Rubin test
        result = rubin_randomness_test(
            sequence, self.subseqsize, self.treatpos, self.outpos,
            alphabet_size=self.alphabet_size, alpha=self.alpha
        )

        # Build calculations
        calculations = []
        if result["p_value"] is not None:
            calculations.append(
                make_calculation("probability value", f"{result['p_value']:.6f}",
                                 precision="6")
            )
        if result["z_score"] is not None:
            calculations.append(
                make_calculation("z score", f"{result['z_score']:.6f}", precision="6")
            )
        if result["avg_distance"] is not None:
            calculations.append(
                make_calculation("average distance", f"{result['avg_distance']:.6f}",
                                 precision="6")
            )
        calculations.append(
            make_calculation("number of matched pairs", str(result["n_pairs"]),
                             data_type="signed 32-bit integer")
        )
        calculations.append(
            make_calculation("number of outcome positions",
                             str(result["num_outcome_bits"]),
                             data_type="signed 32-bit integer")
        )
        calculations.append(
            make_calculation("null mismatch probability",
                             f"{result['null_p_mismatch']:.6f}", precision="6")
        )

        # Build criteria
        passed = result["interpretation"] == "Random"
        criteria = [
            make_criterion(
                f"probability value >= {self.alpha:.6f} (significance level)",
                passed
            )
        ]

        evaluation = "pass" if passed else "fail"
        report.add_test_to_configuration(
            1, bitstream_id, calculations=calculations,
            criteria=criteria, evaluation=evaluation
        )

    def finalize(self, report, num_bitstreams):
        config = report.get_configuration(1)
        if config is None:
            return

        all_pass = all(t["evaluation"] == "pass" for t in config["tests"])
        config_eval = "pass" if all_pass else "fail"

        report.add_criterion_to_configuration(
            1, "All tests in configuration passed", all_pass
        )
        report.set_configuration_evaluation(1, config_eval)

        report.add_report_criterion("All configurations passed", all_pass)
        report.set_evaluation(config_eval)


# =================================================================================================
#  Main
# =================================================================================================

if __name__ == "__main__":
    sys.exit(steer_run(RubinCausalModelTest()))
