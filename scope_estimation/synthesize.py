#!/usr/bin/env python3
"""
Combine the raw counts (results.json), the calibration recall, and the manual
precision labels (precision_labels.json) into final triangulated estimates.
Writes scope_estimation/synthesis.json and prints a summary table.

No network calls. Pure arithmetic over the saved measurements, so the headline
numbers are reproducible from the committed JSON.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion. Returns (p, lo, hi)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def main() -> None:
    res = json.loads((HERE / "results.json").read_text())
    lab = json.loads((HERE / "precision_labels.json").read_text())

    counts = res["A_tier_counts"]
    denom = res["C_pmc_oa_denominator"]
    cal = res["A_calibration"]
    in_oa = cal["in_oa_subset"]          # 46: known PKDB papers actually in the OA subset

    out: dict = {}

    # --- Precision (Wilson CI) from the manual samples ---
    prec = {}
    for tier in ("medium", "broad"):
        k, n = lab[tier]["n_annotatable"], lab[tier]["n_sampled"]
        p, lo, hi = wilson(k, n)
        prec[tier] = {"k": k, "n": n, "precision": round(p, 3),
                      "ci95": [round(lo, 3), round(hi, 3)]}
    out["precision"] = prec

    # --- Recall vs the 46 OA-subset positives (the achievable denominator) ---
    recall_oa = {}
    for tier, r in cal["tier_recall"].items():
        recall_oa[tier] = round(r["matched"] / in_oa, 3) if in_oa else None
    out["recall_vs_oa_subset"] = {"oa_subset_positives": in_oa, "by_tier": recall_oa}

    # --- Method A estimate: precision x count, then recall-correct ---
    A = {}
    for tier in ("medium", "broad"):
        c = counts[tier]
        p, lo, hi = prec[tier]["precision"], *prec[tier]["ci95"]
        point = c * p
        rec = recall_oa[tier] or 1
        A[tier] = {
            "count": c,
            "precision_adjusted": round(point),
            "precision_adjusted_ci95": [round(c * lo), round(c * hi)],
            "recall_vs_oa": rec,
            "recall_corrected_point": round(point / rec) if rec else None,
        }
    out["A_estimate"] = A

    # --- Method B: capture-recapture population x broad precision (its signal is noisy) ---
    B = res["B_capture_recapture"]
    out["B_estimate"] = {
        "population_any_pk_signal": B["N_hat"],
        "population_ci95": B["ci95"],
        "annotatable_via_broad_precision": round(B["N_hat"] * prec["broad"]["precision"]),
        "note": "N_hat counts any-PK-signal OA papers; multiply by precision to approximate annotatable.",
    }

    # --- Headline: PMC-OA annotatable range (converge A broad-recall-corrected & B x precision) ---
    a_point = A["broad"]["recall_corrected_point"]
    a_lo = round(counts["broad"] * prec["broad"]["ci95"][0] / (recall_oa["broad"] or 1))
    a_hi = round(counts["broad"] * prec["broad"]["ci95"][1] / (recall_oa["broad"] or 1))
    b_point = out["B_estimate"]["annotatable_via_broad_precision"]
    out["HEADLINE_pmc_oa_annotatable"] = {
        "central": a_point,
        "range_low": min(a_lo, b_point) if a_lo < b_point else a_lo,
        "range_high": max(a_hi, b_point),
        "methods": {"A_broad_recall_corrected": a_point,
                    "A_broad_precision_ci": [a_lo, a_hi],
                    "B_capture_x_precision": b_point},
        "prevalence_in_pmc_oa": round(a_point / denom, 6),
    }

    # --- Extrapolation to total annotatable literature (beyond OA) ---
    total = 779
    oa_frac = in_oa / total                     # 46/779 = 5.9% of PKDB papers are in OA subset
    pmc_frac = cal["findable_in_pmc"] / total   # 152/779 in PMC at all (~19.5%)
    out["extrapolation_to_total"] = {
        "pkdb_papers_total": total,
        "pkdb_in_oa_subset": in_oa,
        "oa_fraction_of_pkdb": round(oa_frac, 3),
        "pkdb_in_pmc": cal["findable_in_pmc"],
        "pmc_fraction_of_pkdb": round(pmc_frac, 3),
        "implied_total_via_oa_fraction": round(a_point / oa_frac) if oa_frac else None,
        "caveat": "Highly uncertain: assumes universe OA fraction == PKDB's (PKDB skews old/closed; recent literature is more OA).",
    }

    # --- Backlog ---
    out["backlog"] = {
        "oa_remaining": a_point - in_oa,
        "note_total_remaining": "implied_total minus 779 already annotated; order 10^5 but uncertain",
    }

    (HERE / "synthesis.json").write_text(json.dumps(out, indent=2))

    print("PRECISION      medium %.2f (%.2f-%.2f)   broad %.2f (%.2f-%.2f)" % (
        prec["medium"]["precision"], *prec["medium"]["ci95"],
        prec["broad"]["precision"], *prec["broad"]["ci95"]))
    print("RECALL vs 46 OA positives:", recall_oa)
    print("A medium precision-adj: %s   A broad recall-corrected: %s" % (
        A["medium"]["precision_adjusted"], A["broad"]["recall_corrected_point"]))
    print("B population (any PK signal): %s   x broad precision -> %s" % (
        B["N_hat"], out["B_estimate"]["annotatable_via_broad_precision"]))
    h = out["HEADLINE_pmc_oa_annotatable"]
    print("HEADLINE PMC-OA annotatable ~ %s  (range %s - %s)" % (
        h["central"], h["range_low"], h["range_high"]))
    print("Implied TOTAL annotatable (uncertain): %s" %
          out["extrapolation_to_total"]["implied_total_via_oa_fraction"])
    print("Saved -> synthesis.json")


if __name__ == "__main__":
    main()
