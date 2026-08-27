#!/usr/bin/env python3
"""
Estimate the PKDB-annotatable universe in PMC Open Access.

Implements the methodology in docs/PKDB_SCOPE_ESTIMATION.md and SAVES every query
it runs (verbatim `term` strings) plus every count into scope_estimation/results.json,
so the numbers are reproducible and auditable.

Methods run here (all count-only, no bulk downloads):
  A  esearch tier counts (broad / medium / strict) on db=pmc, OA-filtered
  A' calibration: recall of the 155 known-OA PKDB PMCIDs against each tier
  B  capture-recapture (Chapman) from two independent searches (MeSH vs text-word)
  C  denominator |PMC-OA| for prevalence extrapolation (prevalence sampling is
     documented but not auto-run; see docs)

Usage:
  ingest/.venv/bin/python scope_estimation/estimate_scope.py
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import csv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PKDB_PAPERS = ROOT / "pkdb-api" / "pkdb_papers.txt"
RESULTS = HERE / "results.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
TOOL = "pkdb-scope"
EMAIL = "shlok@gxl.ai"
SLEEP = 0.34  # ~3 req/s, NCBI etiquette without an API key

# --- Query building blocks (the PK signature is derived from pkdb_papers.txt) ---
OA = '"open access"[filter]'
HUMANS = 'Humans[MeSH]'
MESH_PK = '"Pharmacokinetics"[MeSH Terms]'
PK_SIGNAL = (
    '("Pharmacokinetics"[MeSH Terms] OR pharmacokinetics[Subheading] '
    'OR "Area Under Curve"[MeSH] OR "Metabolic Clearance Rate"[MeSH] OR "Half-Life"[MeSH] '
    'OR AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab] '
    'OR "volume of distribution"[tiab] OR "concentration-time"[tiab] OR bioavailability[tiab])'
)
TEXTWORD_PK = (
    '(AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab] '
    'OR "concentration-time"[tiab] OR "volume of distribution"[tiab])'
)

TIERS = {
    "broad": f"{OA} AND {PK_SIGNAL} AND {HUMANS}",
    "medium": f"{OA} AND {MESH_PK} AND {HUMANS}",
    "strict": f"{OA} AND {MESH_PK} AND (AUC[tiab] OR Cmax[tiab] OR clearance[tiab]) AND {HUMANS}",
}

# Capture-recapture: two independent strategies over the SAME PK-OA population.
CAP1 = f"{OA} AND {MESH_PK} AND {HUMANS}"          # MeSH-based
CAP2 = f"{OA} AND {TEXTWORD_PK} AND {HUMANS}"      # text-word-based (no MeSH)
CAP_BOTH = f"({CAP1}) AND ({CAP2})"

QUERY_LOG: list[dict] = []


def esearch_count(term: str) -> int:
    """Return the esearch <Count> for a term on db=pmc, logging the exact query."""
    q = urllib.parse.urlencode(
        {"db": "pmc", "term": term, "retmax": "0", "tool": TOOL, "email": EMAIL}
    )
    url = f"{ESEARCH}?{q}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                n = int(ET.fromstring(r.read()).findtext("Count"))
            break
        except Exception as e:  # noqa: BLE001 - retry transient NCBI failures
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))
    QUERY_LOG.append({"db": "pmc", "term": term, "count": n})
    time.sleep(SLEEP)
    return n


def load_oa_pmcid_numbers() -> list[str]:
    """Numeric PMCIDs (no 'PMC' prefix) for the 155 already-annotated OA papers."""
    nums: list[str] = []
    with PKDB_PAPERS.open(newline="") as f:
        for row in csv.DictReader(f):
            pmc = (row.get("pmcid") or "").strip()
            if pmc.upper().startswith("PMC"):
                nums.append(pmc[3:])
    return nums


def count_matching_ids(numbers: list[str], extra_term: str | None, batch: int = 40) -> int:
    """How many of `numbers` (PMCIDs) match `extra_term`, via batched [pmcid] OR-queries."""
    total = 0
    for i in range(0, len(numbers), batch):
        chunk = numbers[i : i + batch]
        ids = " OR ".join(f"{n}[pmcid]" for n in chunk)
        term = f"({ids})" if not extra_term else f"({ids}) AND ({extra_term})"
        total += esearch_count(term)
    return total


def chapman(n1: int, n2: int, m: int) -> dict:
    """Chapman (bias-corrected Lincoln-Petersen) estimator with 95% CI."""
    N = ((n1 + 1) * (n2 + 1) / (m + 1)) - 1
    var = ((n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m)) / (((m + 1) ** 2) * (m + 2))
    se = math.sqrt(var)
    return {
        "n1": n1, "n2": n2, "overlap": m,
        "N_hat": round(N),
        "se": round(se),
        "ci95": [round(N - 1.96 * se), round(N + 1.96 * se)],
    }


def main() -> None:
    out: dict = {"queries_are_logged_in": "results.json:query_log"}

    print("== Method A: tier counts ==")
    out["A_tier_counts"] = {name: esearch_count(term) for name, term in TIERS.items()}
    for k, v in out["A_tier_counts"].items():
        print(f"  {k:7s} {v:>9,}")

    print("== Method C: PMC-OA denominator ==")
    out["C_pmc_oa_denominator"] = esearch_count(OA)
    print(f"  |PMC-OA| = {out['C_pmc_oa_denominator']:,}")

    print("== Method B: capture-recapture ==")
    n1 = esearch_count(CAP1)
    n2 = esearch_count(CAP2)
    m = esearch_count(CAP_BOTH)
    out["B_capture_recapture"] = chapman(n1, n2, m)
    print(f"  n1={n1:,}  n2={n2:,}  overlap={m:,}  N_hat={out['B_capture_recapture']['N_hat']:,}"
          f"  CI95={out['B_capture_recapture']['ci95']}")

    print("== Method A': calibration against 155 known-OA PKDB papers ==")
    nums = load_oa_pmcid_numbers()
    findable = count_matching_ids(nums, None)
    in_oa = count_matching_ids(nums, OA)
    recall = {}
    for name, term in TIERS.items():
        matched = count_matching_ids(nums, term)
        recall[name] = {"matched": matched, "recall": round(matched / len(nums), 3)}
        print(f"  tier {name:7s}: {matched}/{len(nums)} recall={recall[name]['recall']}")
    out["A_calibration"] = {
        "known_oa_pmcids": len(nums),
        "findable_in_pmc": findable,
        "in_oa_subset": in_oa,
        "tier_recall": recall,
    }
    print(f"  findable in PMC: {findable}/{len(nums)}   in OA subset: {in_oa}/{len(nums)}")

    # Derived PMC-OA estimate for the medium tier (recall-corrected; precision TBD by sampling)
    med = out["A_tier_counts"]["medium"]
    med_recall = recall["medium"]["recall"] or 1
    out["derived"] = {
        "medium_tier_count": med,
        "medium_recall": med_recall,
        "note": "multiply by sampled precision to finalize; recall-correct via /recall",
        "recall_corrected_upper_no_precision": round(med / med_recall) if med_recall else None,
    }

    out["query_log"] = QUERY_LOG
    RESULTS.write_text(json.dumps(out, indent=2))
    print(f"\nSaved {len(QUERY_LOG)} queries + all counts -> {RESULTS}")


if __name__ == "__main__":
    main()
