#!/usr/bin/env python3
# =================================================================================================
# pearl_causal_model_test.py
# STEER wrapper for the Pearl Causal Model MVL Randomness Test
#
# This module adapts the Pearl MVL test to run as a STEER-compatible test program.
# It reads binary entropy data via the STEER CLI contract, runs the Pearl test,
# and outputs a conforming JSON report.
# =================================================================================================

import sys
import os
import math
import numpy as np
from collections import defaultdict

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
from steer_sdk import (
    SteerTest, steer_run, make_calculation, make_criterion,
    STEER_RESULT_SUCCESS
)


# =================================================================================================
#  Pearl MVL core functions (extracted from PCM_MVL_V17.py)
# =================================================================================================

def split_sequence(sequence, subseqsize):
    """Split a sequence into non-overlapping blocks of subseqsize."""
    return [sequence[i:i + subseqsize]
            for i in range(0, len(sequence) - subseqsize + 1, subseqsize)]


def binary_to_nary(bits, base):
    """Convert a list of binary bits into base-k symbols.
    Groups ceil(log2(base)) bits into each k-ary symbol via modular reduction.
    """
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


def build_state_transition_graph(sequence, state_bits):
    """Build a directed edge set from a sliding window over the sequence."""
    edges = set()
    if len(sequence) < state_bits + 1:
        return edges
    for i in range(len(sequence) - state_bits):
        src = tuple(sequence[i:i + state_bits])
        dst = tuple(sequence[i + 1:i + state_bits + 1])
        edges.add((src, dst))
    return edges


def normalize_outcomes_by_treatment(blocks, treatpos, outpos, k=None, anchor_index=0):
    """Normalize outcomes by treatment anchor via modular arithmetic."""
    all_vals = [v for b in blocks for p in outpos for v in ([b[p]] if isinstance(b[p], int) else [b[p]])]
    if k is None:
        k = max(all_vals) + 1 if all_vals else 2
    norm_seq = []
    for b in blocks:
        anchor = b[treatpos[anchor_index]]
        for p in outpos:
            norm_seq.append((b[p] - anchor) % k)
    return norm_seq, k


def compute_jaccard_allsets(edge_sets):
    """Compute all-sets Jaccard: |intersection| / |union|."""
    if not edge_sets:
        return 0.0, 0, 0
    intersection = set(edge_sets[0])
    union = set(edge_sets[0])
    for es in edge_sets[1:]:
        intersection &= es
        union |= es
    if not union:
        return 0.0, 0, 0
    return len(intersection) / len(union), len(intersection), len(union)


def compute_jaccard_pairwise(edge_sets):
    """Compute mean pairwise Jaccard across all non-empty pairs."""
    n = len(edge_sets)
    if n < 2:
        return 0.0, 0, []
    scores = []
    for i in range(n):
        for j in range(i + 1, n):
            if edge_sets[i] and edge_sets[j]:
                inter = len(edge_sets[i] & edge_sets[j])
                union = len(edge_sets[i] | edge_sets[j])
                scores.append(inter / union if union > 0 else 0.0)
    if not scores:
        return 0.0, 0, scores
    return float(np.mean(scores)), len(scores), scores


def pearl_mvl_test(sequence, subseqsize, treatpos, outpos,
                   state_bits=2, alphabet_size=None, alpha=0.05, n_sims=1000):
    """Run the Pearl MVL randomness test on a k-ary sequence.

    Returns a dict with jaccard statistics, p-value, z-score, and interpretation.
    """
    blocks = split_sequence(sequence, subseqsize)
    if not blocks:
        return {"jaccard_similarity": 0.0, "p_value": None, "z_score": None,
                "interpretation": "Random", "num_blocks": 0}

    groups = defaultdict(list)
    for b in blocks:
        key = tuple(b[p] for p in treatpos)
        groups[key].append(b)

    min_out_len = min(len(g) * len(outpos) for g in groups.values())
    if min_out_len <= state_bits:
        state_bits = max(1, min_out_len - 1)

    # Build edge sets per treatment group
    edge_sets, edge_counts, labels = [], [], []
    for tkey, gblocks in groups.items():
        norm_seq, k_eff = normalize_outcomes_by_treatment(
            gblocks, treatpos, outpos, k=alphabet_size, anchor_index=0
        )
        edges = build_state_transition_graph(norm_seq, state_bits)
        if edges:
            edge_sets.append(edges)
            edge_counts.append(len(edges))
            labels.append(tkey)

    if not edge_sets:
        return {"jaccard_similarity": 0.0, "p_value": None, "z_score": None,
                "interpretation": "Random", "num_blocks": len(blocks)}

    # Compute observed Jaccard
    jacc_all, inter_sz, union_sz = compute_jaccard_allsets(edge_sets)
    jacc_pair, n_pairs, _ = compute_jaccard_pairwise(edge_sets)
    observed = jacc_pair

    # Infer k from data
    if alphabet_size is None:
        all_vals = [v for b in blocks for v in b]
        alphabet_size = max(all_vals) + 1 if all_vals else 2

    # Simulate null distribution
    import secrets
    null_jaccards = []
    total_len = len(sequence)
    for _ in range(n_sims):
        rand_seq = [secrets.randbelow(alphabet_size) for _ in range(total_len)]
        rand_blocks = split_sequence(rand_seq, subseqsize)
        rand_groups = defaultdict(list)
        for b in rand_blocks:
            key = tuple(b[p] for p in treatpos)
            rand_groups[key].append(b)

        rand_edge_sets = []
        for tkey, gblocks in rand_groups.items():
            ns, _ = normalize_outcomes_by_treatment(
                gblocks, treatpos, outpos, k=alphabet_size, anchor_index=0
            )
            re = build_state_transition_graph(ns, state_bits)
            if re:
                rand_edge_sets.append(re)
        if len(rand_edge_sets) >= 2:
            rj, _, _ = compute_jaccard_pairwise(rand_edge_sets)
            null_jaccards.append(rj)

    # Compute p-value
    p = None
    z = None
    null_mean = None
    null_std = None
    if null_jaccards and len(null_jaccards) > 1:
        nulls = np.asarray(null_jaccards, dtype=float)
        null_mean = float(np.mean(nulls))
        null_std = float(np.std(nulls, ddof=1))
        diffs = np.abs(nulls - null_mean)
        thr = abs(observed - null_mean)
        p = float((np.sum(diffs >= thr) + 1) / (len(nulls) + 1))
        z = 0.0 if null_std == 0 else float((observed - null_mean) / null_std)

    interp = "Random" if p is None else ("Non-random" if p < alpha else "Random")

    return {
        "jaccard_similarity": float(observed),
        "jaccard_pairwise": float(jacc_pair),
        "jaccard_allsets": float(jacc_all),
        "intersection_size": int(inter_sz),
        "union_size": int(union_sz),
        "p_value": p,
        "z_score": z,
        "null_mean": null_mean,
        "null_std": null_std,
        "alpha": alpha,
        "interpretation": interp,
        "num_blocks": len(blocks),
        "num_treatment_groups": len(groups),
        "state_bits": int(state_bits),
        "edge_counts": edge_counts,
        "avg_edges_per_graph": float(np.mean(edge_counts)) if edge_counts else 0.0,
    }


# =================================================================================================
#  STEER Test Implementation
# =================================================================================================

class PearlCausalModelTest(SteerTest):
    test_name = "pearl causal model"
    program_name = "pearl_causal_model_test"
    program_version = "1.0.0"
    test_description = (
        "Pearl Causal Model MVL Randomness Test. Uses state-transition graph "
        "Jaccard similarity across treatment groups to detect non-randomness."
    )

    def __init__(self):
        self.bitstream_count = 1
        self.bitstream_length = 1000000
        self.alpha = 0.01
        self.alphabet_size = 3
        self.subseqsize = 6
        self.state_bits = 2
        self.treatpos = [0, 1]
        self.outpos = [2, 3, 4, 5]
        self.n_sims = 200

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
            {"name": "state bits", "data type": "signed 32-bit integer",
             "default": "2", "minimum": "1"},
            {"name": "treatment positions", "data type": "utf-8 string",
             "default": "0,1"},
            {"name": "outcome positions", "data type": "utf-8 string",
             "default": "2,3,4,5"},
            {"name": "null simulations", "data type": "signed 32-bit integer",
             "default": "200", "minimum": "10"},
        ]

    def init_test(self, params):
        self.bitstream_count = params.get_int("bitstream count")
        self.bitstream_length = params.get_int("bitstream length")
        self.alpha = params.get_float("significance level (alpha)")

        if params.has("alphabet size"):
            self.alphabet_size = params.get_int("alphabet size")
        if params.has("subsequence size"):
            self.subseqsize = params.get_int("subsequence size")
        if params.has("state bits"):
            self.state_bits = params.get_int("state bits")
        if params.has("treatment positions"):
            self.treatpos = [int(x) for x in params.get_string("treatment positions").split(",")]
        if params.has("outcome positions"):
            self.outpos = [int(x) for x in params.get_string("outcome positions").split(",")]
        if params.has("null simulations"):
            self.n_sims = params.get_int("null simulations")

    def get_configuration_count(self):
        return 1

    def execute(self, report, bitstream_id, buffer, num_zeros, num_ones):
        # Convert binary buffer to k-ary sequence
        bits = []
        for byte in buffer:
            for bit_pos in range(7, -1, -1):
                bits.append((byte >> bit_pos) & 1)

        sequence = binary_to_nary(bits, self.alphabet_size)

        # Run Pearl test
        result = pearl_mvl_test(
            sequence, self.subseqsize, self.treatpos, self.outpos,
            state_bits=self.state_bits, alphabet_size=self.alphabet_size,
            alpha=self.alpha, n_sims=self.n_sims
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
        calculations.append(
            make_calculation("jaccard similarity (pairwise)",
                             f"{result['jaccard_similarity']:.6f}", precision="6")
        )
        calculations.append(
            make_calculation("jaccard similarity (all-sets)",
                             f"{result['jaccard_allsets']:.6f}", precision="6")
        )
        calculations.append(
            make_calculation("number of treatment groups",
                             str(result.get("num_treatment_groups", 0)),
                             data_type="signed 32-bit integer")
        )
        calculations.append(
            make_calculation("number of blocks", str(result["num_blocks"]),
                             data_type="signed 32-bit integer")
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
        # Determine configuration-level evaluation from individual tests
        config = report.get_configuration(1)
        if config is None:
            return

        all_pass = all(t["evaluation"] == "pass" for t in config["tests"])
        config_eval = "pass" if all_pass else "fail"

        report.add_criterion_to_configuration(
            1, "All tests in configuration passed", all_pass
        )
        report.set_configuration_evaluation(1, config_eval)

        # Overall report
        report.add_report_criterion("All configurations passed", all_pass)
        report.set_evaluation(config_eval)


# =================================================================================================
#  Main
# =================================================================================================

if __name__ == "__main__":
    sys.exit(steer_run(PearlCausalModelTest()))
