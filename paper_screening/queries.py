"""NCBI query terms for PKDB-annotatable paper discovery.

Tier vocabulary comes from the 2026-07-08 scope estimation work
(docs/PKDB_SCOPE_ESTIMATE.md, docs/PKDB_SCOPE_ESTIMATION.md): keyword
funnels calibrated against PK-DB's own annotated papers.

Tier 3 ("params") is the recommended default search — best tradeoff of
recall (~50% on known PMC positives) vs precision.
"""
from __future__ import annotations

OA = '"open access"[filter]'
HUMANS = "Humans[MeSH]"

# Broad PK signal (title/abstract + MeSH)
PK = (
    "(pharmacokinetics[MeSH Terms] OR pharmacokinetics[MeSH Subheading] "
    'OR pharmacokinetic*[Title/Abstract] OR "concentration-time"[Title/Abstract])'
)

# Reported PK parameters (title/abstract)
PARAM = (
    '("area under the curve"[Title/Abstract] OR AUC[Title/Abstract] '
    "OR Cmax[Title/Abstract] OR clearance[Title/Abstract] "
    'OR "half-life"[Title/Abstract] OR "volume of distribution"[Title/Abstract] '
    "OR bioavailability[Title/Abstract])"
)

# Clinical / dosing cues (healthy-volunteer skewed — recall cost on patient PK)
DOSE = (
    '("single dose"[Title/Abstract] OR "oral administration"[Title/Abstract] '
    'OR "healthy volunteers"[Title/Abstract] OR "healthy subjects"[Title/Abstract] '
    'OR "steady state"[Title/Abstract])'
)

# Expanded PK signal used by the OA-scope estimator (includes MeSH param headings)
PK_SIGNAL_EXPANDED = (
    '("Pharmacokinetics"[MeSH Terms] OR pharmacokinetics[Subheading] '
    'OR "Area Under Curve"[MeSH] OR "Metabolic Clearance Rate"[MeSH] OR "Half-Life"[MeSH] '
    "OR AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR \"half-life\"[tiab] "
    'OR "volume of distribution"[tiab] OR "concentration-time"[tiab] OR bioavailability[tiab])'
)

# Named tiers for search. Values are PubMed/PMC esearch `term` fragments
# (without the optional OA filter — that is layered by the pipeline).
TIERS: dict[str, str] = {
    # Tier 1 — loose ceiling
    "broad": PK,
    # Tier 2 — human-restricted
    "human": f"{PK} AND {HUMANS}",
    # Tier 3 — recommended default
    "params": f"{PK} AND {HUMANS} AND {PARAM}",
    # Tier 4 — high-precision / healthy-volunteer biased floor
    "strict": f"{PK} AND {HUMANS} AND {PARAM} AND {DOSE}",
    # Alias matching scope_estimation medium (MeSH-only, no param requirement)
    "medium": f'"Pharmacokinetics"[MeSH Terms] AND {HUMANS}',
}


def build_term(tier: str, *, oa_only: bool = True, extra: str | None = None) -> str:
    """Compose a full esearch term for db=pmc."""
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; choose from {sorted(TIERS)}")
    parts = [TIERS[tier]]
    if oa_only:
        parts.insert(0, OA)
    if extra:
        parts.append(f"({extra})")
    return " AND ".join(parts)
