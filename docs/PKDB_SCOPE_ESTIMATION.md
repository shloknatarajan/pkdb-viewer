# Estimating the PKDB-Annotatable Universe in PMC Open Access

How to estimate the *scope* of the addressable literature: how many PMC **Open Access (OA)**
papers exist that PK-DB *could* annotate but hasn't yet — papers reporting the
pharmacokinetic data PK-DB curates (concentration–time curves, AUC, Cmax, clearance,
half-life, volume of distribution).

> **TL;DR** — There is no single API that returns "the number of annotatable PK papers." You
> estimate it by triangulating independent methods: (A) a direct NCBI **esearch count** over
> PMC-OA with a PK query, calibrated against papers PK-DB already annotated; (B)
> **capture–recapture** from two independent searches; (C) **prevalence extrapolation**. The
> dominant caveat is measured, not assumed: **only 46/779 (5.9%) of papers PK-DB has *already*
> annotated are in the PMC Open Access subset** (152/779 = 19.5% are in PMC at all) — so the OA
> subset is a *minority slice* of the true annotatable literature.
>
> **Headline result (measured 2026-07-08):** the PMC Open Access subset holds on the order of
> **~15,000 PKDB-annotatable papers** (defensible range ≈ **4,000–45,000**; Method A broad tier
> ≈ 15k, Method B capture–recapture ≈ 23k). PK-DB has annotated **46** of them, so the **OA
> backlog is ~15,000 papers**. Extrapolated beyond OA the total annotatable literature is order
> **10⁵ (~250k, highly uncertain)**. Every count, query, and estimate is saved under
> `scope_estimation/` (`results.json`, `precision_labels.json`, `synthesis.json`).

---

## The ground truth we calibrate against

`pkdb_papers.txt` (repo root) is a CSV — `pmid,pmcid,title,abstract` — of the **779 papers
PK-DB has already annotated**. It is the positive/"done" set and the anchor for every method
below. Measured facts:

| Fact | Value | Source |
|---|---|---|
| Curated studies / papers | 803 studies / **779** papers | `pkdb-api/summary.json` |
| Papers with a PMID | 779 (100%) | `pkdb_papers.txt` |
| Papers with a **PMCID** (in PMC) | **155 (19.9%)** | `pkdb_papers.txt` |
| Papers with an abstract | 720 | `pkdb_papers.txt` |
| Studies by licence | 88 open / 715 closed | `pkdb-api/studies_full.json` |

**Abstract term signature** (fraction of the 779 abstracts containing the term) — this is the
empirical basis for the search query in Method A, not a guess:

| Term | Coverage | Term | Coverage |
|---|---|---|---|
| plasma | 43% | clearance | 23% |
| dose | 41% | AUC | 22% |
| pharmacokinetic | 40% | CYP | 20% |
| concentration | 40% | half-life | 13% |
| healthy | 37% | volume of distribution | 5% |

### Why 19.9% is the headline caveat
PK-DB is dominated by **older and closed-access** PK studies (many pre-2000 clinical
pharmacology papers). Four out of five already-annotated papers are **not in PMC**. Therefore:

- The literal question ("how many **PMC-OA** papers can we annotate") has a *bounded, smaller*
  answer than the true annotatable universe.
- To go from a PMC-OA estimate to a **total annotatable** estimate you divide by the OA
  fraction (≈0.199 historically; higher for recent years — see Method E). That extrapolation
  is much less certain and must be labelled as such.

---

## Results (measured 2026-07-08)

Produced by `scope_estimation/estimate_scope.py` (counts + calibration),
`scope_estimation/sample_precision.py` (abstract samples), and
`scope_estimation/synthesize.py` (arithmetic). Re-run those to refresh.

### Raw esearch counts (db=pmc)

| Query | Count |
|---|---:|
| PMC Open Access subset denominator (`"open access"[filter]`) | **7,831,626** |
| Method A — broad tier (OA + any PK signal + Humans) | 97,961 |
| Method A — medium tier (OA + `Pharmacokinetics[MeSH]` + Humans) | 18,413 |
| Method A — strict tier (medium + AUC/Cmax/clearance[tiab]) | 5,757 |
| Method B — capture 1 (MeSH) `n1` | 18,413 |
| Method B — capture 2 (text-word) `n2` | 71,482 |
| Method B — overlap `m` | 6,363 |

### Calibration against the 779 already-annotated papers

| Measurement | Value |
|---|---:|
| Papers with a PMCID (findable in PMC) | 152 / 779 (19.5%) |
| Papers **in the OA subset** (`"open access"[filter]`) | **46 / 779 (5.9%)** |
| Broad-tier recall vs the 46 OA positives | 33/46 = **71.7%** |
| Medium-tier recall vs the 46 OA positives | 14/46 = 30.4% |
| Strict-tier recall vs the 46 OA positives | 9/46 = 19.6% |

> **Key finding:** having a PMCID ≠ being in the OA subset. Two-thirds of PK-DB's PMC papers
> are *not* in the redistributable OA subset. The OA subset is where clean full text lives, so
> it is the honest denominator — but it captures only ~6% of what PK-DB has curated.

### Precision (manual classification of sampled hits → `precision_labels.json`)

Each sampled abstract was judged: *does it report human PK parameters PKDB curates
(AUC/Cmax/clearance/half-life/Vd or a concentration–time curve)?*

| Tier | Annotatable / sampled | Precision (Wilson 95% CI) |
|---|---:|---|
| medium | 5 / 30 | **0.17** (0.07–0.34) |
| broad | 2 / 18 | **0.11** (0.03–0.33) |

Precision is low because the query terms are polysemous in the OA corpus:
- **"AUC" = ROC area-under-curve** in the flood of recent ML/radiomics/diagnostic papers.
- **"clearance"** = bacterial/viral/renal clearance in non-PK clinical papers.
- MeSH `Pharmacokinetics` is attached to **nanomedicine, drug-delivery, and animal/in-vitro
  formulation** studies that report no human PK values.
The OA subset skews to **recent** (2023–2025) papers, which are disproportionately ML and
formulation work — not the classic clinical-PK studies PK-DB curates.

### Triangulated estimate → `synthesis.json`

| Method | PMC-OA annotatable estimate |
|---|---:|
| A, broad tier: count × precision, ÷ recall (97,961 × 0.11 ÷ 0.717) | **~15,200** |
| A, broad tier CI (precision CI, recall-corrected) | 4,200 – 44,800 |
| A, medium tier: count × precision (18,413 × 0.17) — a subset | ~3,100 |
| B, capture–recapture population × broad precision (206,832 × 0.11) | **~23,000** |

**Headline — PMC-OA annotatable ≈ 15,000 papers** (defensible range ~4,000–45,000). A and B
agree to within ~1.5×. Implied prevalence in the OA subset ≈ **0.19%**.

> **Why Method C (random-sample prevalence) was not run to a number:** at ~0.19% prevalence, a
> random sample of the 7.8M OA papers would need thousands of classifications to catch enough
> positives for a tight CI. The annotatable class is too rare for naive random sampling —
> query-enriched sampling (Method A) is the right tool. This is itself a result: the target is
> a needle in the OA haystack.

### Backlog and total-literature extrapolation

- **OA backlog** = ~15,000 − 46 already done ≈ **~15,000 annotatable OA papers untouched**.
- **Total annotatable (beyond OA)** = 15,200 ÷ 0.059 (PK-DB's OA fraction) ≈ **~257,000** —
  order 10⁵, but **highly uncertain**: it assumes the whole literature's OA fraction equals
  PK-DB's historical 5.9%. PK-DB skews old/closed; recent PK papers are far more OA (Method E),
  so the true multiplier is smaller and this is an upper-leaning figure. Treat as
  "order-of-magnitude 100k+," not a point estimate.

---

## Method A — Direct PMC esearch count (primary)

NCBI E-utilities `esearch` returns `<Count>` = the number of records matching a query, with
**no downloads**. Point it at **db=pmc**, restrict to the OA subset, and apply a PK signature.

### The query pieces

- **OA subset filter:** `"open access"[filter]` — the PMC Open Access Subset. (Verify the
  exact filter token against current PMC docs before quoting; `pmc open access[filter]` and
  `"loattrfree full text"[filter]` are related-but-different scopes.)
- **PK-model signal** (from the signature above + MeSH):
  ```
  "Pharmacokinetics"[MeSH Terms] OR pharmacokinetics[Subheading]
  OR "Area Under Curve"[MeSH] OR "Metabolic Clearance Rate"[MeSH] OR "Half-Life"[MeSH]
  OR AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab]
  OR "volume of distribution"[tiab] OR "concentration-time"[tiab] OR bioavailability[tiab]
  ```
- **Human/clinical filter** (PK-DB is human/clinical): `Humans[MeSH]`.

### Report a tiered range (each with its own Count)

| Tier | `term` (conceptually) | What it bounds |
|---|---|---|
| Broad | OA `AND` (any single PK term) `AND` Humans | Upper bound (loose) |
| Medium | OA `AND` `Pharmacokinetics[MeSH]` `AND` Humans | Central estimate |
| Strict | OA `AND` `Pharmacokinetics[MeSH]` `AND` (AUC OR Cmax OR clearance)[tiab] `AND` Humans | Lower bound (high-precision) |

### Runnable count (paste and run — reproduces the headline number)

```bash
python3 - <<'PY'
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EMAIL  = "shlok@gxl.ai"   # NCBI politeness; use your own

PK_SIGNAL = ('("Pharmacokinetics"[MeSH Terms] OR pharmacokinetics[Subheading] '
             'OR "Area Under Curve"[MeSH] OR "Metabolic Clearance Rate"[MeSH] OR "Half-Life"[MeSH] '
             'OR AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab] '
             'OR "volume of distribution"[tiab] OR "concentration-time"[tiab] OR bioavailability[tiab])')

TIERS = {
  "broad" : f'"open access"[filter] AND {PK_SIGNAL} AND Humans[MeSH]',
  "medium": '"open access"[filter] AND "Pharmacokinetics"[MeSH Terms] AND Humans[MeSH]',
  "strict": ('"open access"[filter] AND "Pharmacokinetics"[MeSH Terms] '
             'AND (AUC[tiab] OR Cmax[tiab] OR clearance[tiab]) AND Humans[MeSH]'),
}

def count(term):
    q = urllib.parse.urlencode({"db":"pmc","term":term,"retmax":"0",
                                "tool":"pkdb-scope","email":EMAIL})
    with urllib.request.urlopen(f"{EUTILS}?{q}", timeout=60) as r:
        return int(ET.fromstring(r.read()).findtext("Count"))

for name, term in TIERS.items():
    print(f"{name:7s} PMC-OA count = {count(term):>8,}")
PY
```

### Calibration — turn a raw Count into an estimate

A Count is not an estimate; it is `true_positives / precision`, missing whatever the query
fails to catch. Correct it with the ground-truth set:

1. **Recall** — of the known PK-DB PMCIDs, how many does the query return? Only **46 of the
   155** PK-DB PMCIDs are actually in the OA subset, so recall against the OA-restricted tiers
   is `matched / 46` (measured: broad 72%, medium 30%, strict 20%). Intersect by adding
   `AND (6777419[pmcid] OR …)`. **Gotcha:** the PMC `[pmcid]` field wants the **numeric** form
   (`6777419[pmcid]`) — `PMC6777419[pmcid]` returns 0.
2. **Precision** — sample ~50 hits *not* in PK-DB, classify each against the PK-DB data model
   (does it report AUC/Cmax/clearance/half-life/Vd or a concentration–time curve?). `precision
   = annotatable / 50`.
3. **Estimate:**
   ```
   annotatable_OA ≈ Count × precision
   recall-corrected ≈ (Count × precision) / recall   # if the query misses known positives
   ```

Reuse `pkdb-api/resolve_pmcids.py`'s NCBI ID-Converter batch pattern to map any PMIDs↔PMCIDs
needed for the recall intersection.

---

## Method B — Capture–recapture (Chapman estimator)

Estimate total PK-OA papers **N** from the overlap of **two independent captures of the same
population**. Standard ecology/epidemiology technique for counting an unknown population.

> ⚠️ Do **not** pair PK-DB with PharmGKB. They are near-**disjoint** (overlap ≈ 0 in
> `pmcid_articles.csv`): PK-DB is pharmacokinetics, PharmGKB is pharmacogenomics. Their union
> is not the PK population, so their overlap does not estimate it.

Use two **independent search strategies** over PMC-OA instead:

- **Capture 1** (MeSH-based): `"open access"[filter] AND "Pharmacokinetics"[MeSH] AND Humans[MeSH]`
- **Capture 2** (text-word-based, no MeSH): `"open access"[filter] AND (AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab] OR "concentration-time"[tiab]) AND Humans[MeSH]`
- `n1`, `n2` = each capture's PMCID-set size; `m` = size of their intersection.
- **Chapman estimator** (bias-corrected Lincoln–Petersen):
  ```
  N̂ = ((n1 + 1)(n2 + 1) / (m + 1)) − 1
  Var(N̂) = (n1+1)(n2+1)(n1−m)(n2−m) / ((m+1)² (m+2))
  95% CI ≈ N̂ ± 1.96·sqrt(Var(N̂))
  ```

Fetch each capture's PMCIDs (esearch `usehistory=y` + efetch/esummary, or `retmax` paging),
intersect locally, then plug into the formula.

**→ Measured (2026-07-08):** `n1=18,413`, `n2=71,482`, `m=6,363` → **N̂ = 206,832** (95% CI
202,909–210,756). The observed overlap (6,363) is *lower* than independence would predict
(≈13,400 if N≈98k), i.e. the two signals are mildly **anti-correlated** — text-word hits
(`AUC`/`clearance`) are heavily non-PK, so N̂ inflates. N̂ counts *any-PK-signal* OA papers,
not annotatable ones; multiplying by the broad-tier precision (0.11) gives ≈**23,000**
annotatable — consistent with Method A. Treat N̂ itself as an upper bound on the signal pool.

**Robustness pairing:** Capture 1 = PK-DB's OA positives (a curated "mark"); Capture 2 = an
automated classifier's OA hits (Method C's classifier). Overlap → N̂. The main threat is the
**independence assumption**; here it manifests as the anti-correlation above.

---

## Method C — Prevalence extrapolation (sample-and-classify)

The most assumption-light method and the best independent check on Method A.

1. **Denominator** = size of the PMC-OA subset from NCBI's authoritative OA file list:
   ```
   https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv        # commercial + non-commercial OA
   # (line count − 1 header = |PMC-OA|; on the order of a few million)
   ```
2. **Random sample** 500–1,000 PMCIDs from that list.
3. **Classify** each as PK-DB-annotatable using a classifier seeded on the `pkdb_papers.txt`
   signature (keyword rules, or an LLM prompt given a few positive/negative abstracts from the
   779). Get prevalence `p̂ = annotatable / sampled`.
4. **Estimate + interval** (Wilson binomial CI, robust for small `p`):
   ```
   estimate = p̂ × |PMC-OA|
   Wilson CI on p̂ → multiply both bounds by |PMC-OA|
   ```

Because prevalence is small, use ≥500 samples so the CI is meaningful. This method needs no
query-term engineering and so is not biased by term choice the way A is.

**→ Measured (2026-07-08):** the denominator is **|PMC-OA| = 7,831,626**. But the implied
prevalence of annotatable papers is only ~**0.19%** (15k / 7.8M), so a random sample would
need thousands of classifications to catch enough positives — the class is a needle in the
haystack. **Method C is therefore impractical as a standalone estimator here**; query-enriched
sampling (Method A) is the correct approach. The denominator is still used for the extrapolation.

---

## Method D — Positive-set snowball / saturation (sanity bound)

Bounds the *reachable connected* universe rather than the absolute one.

- Seed with the **779 PK-DB PMIDs**.
- Expand via references + citing articles + "similar articles":
  - NCBI `elink` (`db=pubmed`, `linkname=pubmed_pubmed` for neighbors, `pubmed_pmc_refs` for
    citing), or
  - **OpenAlex** / **iCite** (richer citation graph, one HTTP call per seed).
- Keep only PMC-OA neighbors; classify with Method C's classifier.
- Plot **new annotatable found per expansion round**; the curve's **asymptote** approximates
  the reachable universe. If it saturates well below A/B/C, the query in A is too broad; if it
  keeps climbing, A is too narrow.

---

## Method E — Temporal / growth model (fixes the OA-fraction multiplier)

The measured OA-subset fraction (5.9%) and PMC fraction (19.5%) are *historical averages* over
PK-DB's old-skewed corpus; recent papers are far more likely OA, so these understate OA
coverage going forward and make the total-literature extrapolation an upper bound.

- Facet Method A's medium-tier count by publication year (`AND ("2015"[pdat] : "2025"[pdat])`,
  etc.) → **annual inflow** of new PK-OA papers = backlog growth rate.
- Compute the OA fraction **per year** among PK-DB papers (bucket the 779 by `reference_date`,
  fraction with a PMCID per bucket) → **OA-fraction(year)**.
- Use the recent-year OA fraction (not 0.199) as the multiplier when extrapolating a *recent*
  PMC-OA estimate to a total.

---

## Triangulation & headline numbers

Report **two figures with ranges**, never a single point (see the **Results** section above
for the measured values):

1. **PMC-OA annotatable scope** (the literal question) = the converged range across A
   (Count × precision, recall-corrected) and B (Chapman N̂ × precision). **Measured ≈ 15,000
   (range 4,000–45,000)**; A and B agree to ~1.5×. C is impractical standalone here (rarity).
2. **Implied total annotatable scope** = PMC-OA estimate ÷ OA-fraction (0.059 measured, or the
   recent-year fraction from E). **Measured ≈ 250k, order 10⁵**, extrapolation *beyond* OA —
   the least certain figure.

**Remaining backlog** (what's actually left to do), using the *measured* already-annotated
counts (46 in OA subset, 779 total):

```
remaining_OA    = ~15,000 − 46   ≈ ~15,000   # OA subset backlog (clean full text)
remaining_total = ~250,000 − 779 ≈ 10⁵       # order of magnitude, uncertain
```

---

## Reproduce

```bash
ingest/.venv/bin/python scope_estimation/estimate_scope.py      # counts + calibration -> results.json
ingest/.venv/bin/python scope_estimation/sample_precision.py medium 50   # -> sample_medium.jsonl
ingest/.venv/bin/python scope_estimation/sample_precision.py broad 50    # -> sample_broad.jsonl
# classify the samples by hand/LLM -> precision_labels.json, then:
ingest/.venv/bin/python scope_estimation/synthesize.py          # triangulated estimate -> synthesis.json
```

`results.json` contains the **verbatim `term` of every esearch query run** (`query_log`), so
the numbers are fully auditable.

## Practical notes

- **NCBI etiquette:** include `tool=` and `email=`, ≤3 req/s without a key (10/s with an
  `api_key`), retry on 429. `pkdb-api/resolve_pmcids.py` already implements a compliant
  batch+backoff pattern to copy.
- **db choice:** count in **`pmc`** (full-text corpus) for the OA question. Counting in
  `pubmed` answers a different, larger question (indexed abstracts, mostly not OA).
- **Query drift:** PMC filter tokens and MeSH terms change; re-verify tokens and re-run the
  calibration whenever quoting a fresh number. Record the run date next to any figure, as
  `PKDB_DATA_SOURCES.md` does.

## Attribution & terms

PK-DB: Grzegorzewski et al., *Nucleic Acids Res.* 2021,
[doi:10.1093/nar/gkaa990](https://doi.org/10.1093/nar/gkaa990). PMC OA data used under NCBI's
Open Access Subset terms; attribution to original publishers required.
