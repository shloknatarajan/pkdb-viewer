# Paper screening for PK-DB annotation

Keyword- and logic-based pipeline that finds papers worth annotating into
[PK-DB](https://pk-db.com/). **No LLM calls** — NCBI search + lexical scoring only.

Built from the 2026-07-08 scope / precision findings in `docs/PKDB_SCOPE_ESTIMATE.md`
and `docs/PKDB_SCOPE_ESTIMATION.md`.

Readable config (retrieval tiers + scoring rules):
[`pkdb_annotation_search.yaml`](pkdb_annotation_search.yaml).

## What it does

1. **Search** PMC with a calibrated keyword funnel (`broad` → `human` → `params` → `strict`).
2. **Fetch** titles/abstracts via NCBI E-utilities.
3. **Filter out** papers already curated in PK-DB (`pkdb_papers.txt` / `pkdb-api/pmid_to_pmcid.csv`).
4. **Score** each abstract with rule-based positive/negative signals (clinical PK vs
   ML/ROC-AUC traps, non-PK “clearance”, etc.).
5. **Rank** and write JSONL / CSV candidates.

The same scorer can also run over a **local folder of markdown papers**.

## Quick start

```bash
# Recommended: tier-3 "params" over the PMC Open Access Subset
ingest/.venv/bin/python -m paper_screening search --tier params --limit 100 \
  --out paper_screening/out/candidates.jsonl \
  --csv paper_screening/out/candidates.csv

# Score downloaded markdown papers
ingest/.venv/bin/python -m paper_screening local \
  --dir variantAnnotations/papers --limit 200 \
  --out paper_screening/out/local_ranked.jsonl

# Inspect one abstract
ingest/.venv/bin/python -m paper_screening score \
  --title "Pharmacokinetics of midazolam in healthy volunteers" \
  --abstract "Plasma concentrations were measured after a single oral dose. Cmax, AUC and half-life were reported."

# Print the exact NCBI terms
ingest/.venv/bin/python -m paper_screening tiers
```

Optional env vars: `NCBI_EMAIL`, `NCBI_API_KEY` (raises rate limit ~3 → 10 req/s).

## Tiers

| Tier | Meaning | When to use |
|---|---|---|
| `broad` | any PK mention | upper-bound recall |
| `human` | + Humans MeSH | drop animal/in-vitro-only |
| **`params`** | + AUC/Cmax/clearance/half-life/Vd/bioavailability | **default** |
| `strict` | + dosing/healthy-volunteer cues | highest precision, misses patient-pop PK |
| `medium` | MeSH Pharmacokinetics only (scope_estimation alias) | broader OA sweep |

Default search is **OA-subset only** (`"open access"[filter]`). Pass `--all-pmc` for all PMC full text (not necessarily redistributable).

## Scorer signals (summary)

**Positive:** pharmacokinetics, concentration-time, Cmax/Tmax/AUC/half-life/Vd/bioavailability/clearance, healthy volunteers / single dose / oral administration, plasma concentration-time curves.

**Hard reject:** machine-learning / radiomics / ROC context where “AUC” is clearly not PK; bacterial/viral/tumor clearance without PK framing.

**Soft penalty:** nanoparticle / in-vitro / murine / narrative reviews (can still pass if PK signals are strong).

A hit **passes** at score ≥ 4 with at least one of: PK core framing, (2+ params + clinical cue), or (curve language + a param).

## Python API

```python
from paper_screening import search_candidates, screen_local_dir, score_text

cands, meta = search_candidates(tier="params", limit=50)
for c in cands[:5]:
    print(c.score.score, c.pmcid, c.title)

print(score_text("Pharmacokinetics of X", "Cmax and AUC after a single oral dose in healthy volunteers.").as_dict())
```

## Outputs

JSONL lines are one candidate each (plus an optional leading `_meta` record). Useful fields:
`score`, `grade` (`strong`/`moderate`/`weak`/`reject`), `passed`, `pmid`, `pmcid`, `title`, `reasons`.
