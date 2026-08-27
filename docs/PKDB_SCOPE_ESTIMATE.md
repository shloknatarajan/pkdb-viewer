# How many PMC papers could PK-DB annotate?

Estimating the *scope* — the total pool of PubMed Central papers that plausibly
contain annotatable pharmacokinetic data — so we can size the runway beyond the
**803** studies PK-DB has curated so far.

> **TL;DR** — Calibrating PMC search queries against PK-DB's own known papers, the
> candidate pool is on the order of **20,000 – 100,000 papers**, with a best
> single estimate of **~40,000** human PK studies that report PK parameters
> (~20,000 of them in the machine-mineable CC-licensed Open Access Subset).
> PK-DB's 803 curated studies are **~2% of the mid estimate** → roughly a **50×
> runway**. Numbers computed 2026-07-08; reproduce with
> `scope_estimation/estimate_pmc_scope.py`.

---

## The core idea: query-and-calibrate

You cannot ask PMC "how many papers have annotatable PK data" directly — there is
no such flag. Any keyword/MeSH query is a proxy that both **misses** real PK
papers (low recall) and **includes** non-annotatable ones (reviews, in-vitro,
methods — low precision). A raw hit count is therefore meaningless on its own.

The fix: **PK-DB is its own labeled answer key.** Its 803 curated studies are, by
definition, annotatable. **152 of them live in PMC** (`pkdb-api/pmid_to_pmcid.csv`).
So for any candidate query we can measure its **recall** — what fraction of those
152 known-good papers it actually returns — and correct the raw count:

```
recall-corrected estimate  =  (papers the query returns)  /  (recall on the 152)
```

A query that finds 76% of PK-DB's own papers and returns 128k papers implies a
true pool near 128k / 0.76 ≈ 169k *of that breadth*. Tightening the query trades
recall for precision, and the corrected estimate falls toward the annotatable
core.

### Two "open access" universes — they differ 2×

A subtle but important split. Having a **PMCID** (free full text in PMC) is *not*
the same as being in the **Open Access Subset** (`open access[filter]` — the CC
licenses that permit text mining and redistribution):

| | count | PK-DB papers inside |
|---|---|---|
| All PMC full text | 12.16 M | 152 / 152 (100%) |
| Open Access Subset (`open access[filter]`) | 7.83 M | 46 / 152 (**30%**) |

Only **6% of PK-DB's 803 studies** (46) sit in the license-clean subset. If the
annotation pipeline needs redistributable full text, the addressable universe is
~2× smaller than "anything with a PMCID." Both columns are reported below.

---

## Result: the calibrated funnel

Each tier adds a constraint (built from PK-DB's characteristic vocabulary:
pharmacokinetics MeSH/subheading, `concentration-time`, `AUC/Cmax/clearance/
half-life/Vd`, human dosing language). Recall is measured against the 152.

| query tier | what the search does (query gist) | recall | ALL-PMC hits → **recall-scaled** | OA-subset hits → **recall-scaled** |
|---|---|---:|---:|---:|
| 1 · any PK mention | PK anywhere: `pharmacokinetics[MeSH/Subheading] OR pharmacokinetic*[tiab] OR "concentration-time"[tiab]` | 76% | 128,298 → **169,576** | 72,968 → **96,445** |
| 2 · + humans | tier 1 **AND** `humans[MeSH]` — drops animal/in-vitro-only work | 68% | 74,830 → **109,367** | 40,388 → **59,029** |
| 3 · + reported PK params | tier 2 **AND** a PK metric in text: `AUC OR Cmax OR clearance OR "half-life" OR "volume of distribution"[tiab]` | 50% | 21,256 → **42,512** | 11,434 → **22,868** |
| 4 · + dosing / clinical | tier 3 **AND** dosing/clinical cue: `"single dose" OR "oral administration" OR "healthy volunteers/subjects" OR "steady state"[tiab]` | 32% | 5,715 → **17,728** | 2,707 → **8,397** |

**Reading it.** Tier 1 is the outer ceiling (anything PK-flavoured). Tier 4 is a
high-precision floor (looks like a classic clinical PK study) but already drops
2/3 of PK-DB's real papers, so its corrected estimate is the most uncertain.
**Tier 3 — human studies reporting PK parameters — is the best single anchor:**
it matches what PK-DB actually extracts and still recalls half the known set.

**Headline scope: ~40,000 candidate papers (all-PMC), ~20,000 in the OA-subset**,
bracketed by ~18k (strict) and ~100k (broad).

Against **803 curated** (152 in PMC), PK-DB has mined well under **2%** of even the
conservative pool. The bottleneck is curation effort, not paper availability.

---

## Recommended refinement

**Abstract text classifier — best future refinement.** The sharpest scope number
would come from a model, not keywords. We have **720 PK-DB abstracts** (positives,
in `pkdb-api/pkdb_papers.txt`) — train a classifier (embeddings or an LLM judge) on those
vs. random PMC abstracts, score a random sample of PMC, and multiply the positive
rate by 12.16 M. This replaces the leaky keyword *precision* with a learned one and
would tighten the ±5× band above to perhaps ±2×. Recommended next step.

---

## Caveats

- **Precision is not yet measured.** Every estimate is `hits / recall`; it assumes
  the query's precision on the general corpus matches its precision on PK-DB
  papers. Tier 1 certainly includes many non-annotatable reviews/in-vitro papers.
  The classifier method above is how you pin precision down.
- **Recall base is 152 papers.** Modest sample; tier-4's 32% recall (≈49 papers) is
  the noisiest cell. Treat single points as order-of-magnitude, not exact.
- **PK-DB's PMC papers skew old** (many 1990s–2000s PMCIDs), which depresses
  OA-subset membership (the subset is richer in recent CC-licensed articles); the
  30% figure is a floor for what *newer* curation would achieve.
- **PMC ⊂ all literature.** This estimates the PMC-reachable pool only. PK-DB also
  curates non-PMC papers (only 20% of its own corpus is in PMC), so the *total*
  annotatable literature is several times larger than the PMC numbers here.

---

## Appendix: the exact queries

Every call is NCBI E-utilities **`esearch`** against **`db=pmc`**, reading
`esearchresult.count`. Endpoint:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
  ?db=pmc&retmode=json&retmax=0&email=<you>&term=<TERM>
```

(POST the `term` for the calibration queries — the 152-PMCID `OR` list overflows a
GET URL. `&api_key=` optional, lifts the rate limit from 3→10 req/s.)

**Reusable term blocks** (referenced as `{PK}`, `{HUM}`, `{PARAM}`, `{DOSE}` below):

```text
{PK}    = (pharmacokinetics[MeSH Terms] OR pharmacokinetics[MeSH Subheading]
           OR pharmacokinetic*[Title/Abstract] OR "concentration-time"[Title/Abstract])
{HUM}   = humans[MeSH Terms]
{PARAM} = ("area under the curve"[Title/Abstract] OR AUC[Title/Abstract] OR Cmax[Title/Abstract]
           OR clearance[Title/Abstract] OR "half-life"[Title/Abstract] OR "volume of distribution"[Title/Abstract])
{DOSE}  = ("single dose"[Title/Abstract] OR "oral administration"[Title/Abstract] OR "healthy volunteers"[Title/Abstract]
           OR "healthy subjects"[Title/Abstract] OR "steady state"[Title/Abstract])
{POS}   = 1364644[pmcid] OR 1365159[pmcid] OR ... (the 152 PK-DB PMCIDs, numeric, no "PMC" prefix, OR-joined)
```

**Universe sizes** (the denominators / context numbers):

| number | `term=` |
|---|---|
| PMC full text = 12,160,893 | `all[sb]` |
| OA-subset = 7,831,626 | `open access[filter]` |
| PK-DB positives in PMC = 152 | `({POS})` |
| PK-DB positives in OA-subset = 46 | `open access[filter] AND ({POS})` |

**Per-tier queries.** For each funnel tier the recall-corrected estimate needs
three counts — recall numerator, all-PMC hits, OA hits — using the `{TIER}` term
in the middle column:

| tier | `{TIER}` term | recall = `({TIER}) AND ({POS})` ÷ 152 | all-PMC hits = `({TIER})` | OA hits = `open access[filter] AND ({TIER})` |
|---|---|---:|---:|---:|
| 1 · any PK mention | `{PK}` | 115/152 = 76% | 128,298 | 72,968 |
| 2 · + humans | `{PK} AND {HUM}` | 104/152 = 68% | 74,830 | 40,388 |
| 3 · + reported PK params | `{PK} AND {HUM} AND {PARAM}` | 76/152 = 50% | 21,256 | 11,434 |
| 4 · + dosing / clinical | `{PK} AND {HUM} AND {PARAM} AND {DOSE}` | 49/152 = 32% | 5,715 | 2,707 |

Recall-scaled value for a cell = hits ÷ recall (e.g. tier 3 all-PMC: 21,256 ÷ 0.50 ≈ 42,512).

**Fully expanded example** — tier 3, all-PMC hits (the `term=`, URL-decoded):

```text
((pharmacokinetics[MeSH Terms] OR pharmacokinetics[MeSH Subheading] OR pharmacokinetic*[Title/Abstract]
 OR "concentration-time"[Title/Abstract]) AND humans[MeSH Terms] AND ("area under the curve"[Title/Abstract]
 OR AUC[Title/Abstract] OR Cmax[Title/Abstract] OR clearance[Title/Abstract] OR "half-life"[Title/Abstract]
 OR "volume of distribution"[Title/Abstract]))
```

**Single-ID field check** (how the `[pmcid]` restriction was validated): the field
takes the **numeric** accession, not the `PMC` prefix — `1368322[pmcid]` → 1 hit,
`PMC1368322[pmcid]` → 0 hits.

---

## Reproduce

```bash
python3 scope_estimation/estimate_pmc_scope.py
# ~1 min, stdlib only; writes scope_estimation/pmc_scope_estimate.json
```

Inputs: `pkdb-api/pmid_to_pmcid.csv` (the 152 labeled positives). The script hits
NCBI E-utilities `esearch` on `db=pmc`, POSTing so the 152-PMCID calibration query
doesn't overflow the URL. Swap the `FUNNEL` query blocks to test other vocabularies.

---

## Per-tier breakdown & ground-truth error analysis

Everything about each tier in one place: what the query does, the numbers, and —
crucially — *which of PK-DB's own 152 in-PMC papers it fails to find*. The missed
papers come from `esearch` `idlist` ∩ positives, with titles from
`pkdb-api/pkdb_papers.txt`.
The misses are **not random**: each constraint has a characteristic blind spot, and
almost every miss is a *true* PK paper lost for a lexical/indexing reason — not a
non-PK paper correctly excluded. This is why the recall correction matters and why
keyword tightening carries a real recall cost.

### Tier 1 · any PK mention

- **Query:** `pharmacokinetics[MeSH/Subheading] OR pharmacokinetic*[tiab] OR "concentration-time"[tiab]`
- **Recall:** 115/152 = **76%** · **ALL-PMC:** 128,298 → 169,576 · **OA-subset:** 72,968 → 96,445
- **Missed: 37 papers — no PK signal at all.** No `pharmacokinetics` MeSH/subheading
  and none of the PK terms in title/abstract. The study *reports* PK data (in
  full-text tables/figures) but the **abstract frames it as something else**:
  - *pharmacodynamics / physiology* — "Evaluation of the central effects of alcohol and caffeine interaction", insulin/glucose counter-regulation studies, omeprazole intragastric-pH studies;
  - *drug metabolism / CYP phenotyping* — "demethylation and glucuronidation of codeine", "CYP2D6 Phenotyping Using Urine, Plasma, and Saliva Metabolic Ratios", "chlorzoxazone as an in vivo measure of CYP2E1";
  - *analytical-method papers* — "A simplified HPLC method for quantification of torsemide … application to a [PK study]" — the abstract is about the assay, PK is the application;
  - *older "kinetics" vocabulary* — indocyanine-green clearance, "measurement of extracellular fluid by … constant infusion".
- **Why:** a **structural blind spot of title/abstract search** — no term-list
  reaches these. Only full-text search (or reading parameter values out of tables) would.

### Tier 2 · + humans

- **Query:** tier 1 **AND** `humans[MeSH]`
- **Recall:** 104/152 = **68%** · **ALL-PMC:** 74,830 → 109,367 · **OA-subset:** 40,388 → 59,029
- **Dropped vs tier 1: 11 papers.** Almost all are explicitly human PK papers
  ("Pharmacokinetics and Safety of iGlarLixi in Healthy Chinese Participants",
  "…lobeglitazone, empagliflozin, and metformin in healthy…") that simply **lack the
  Humans MeSH tag** — mostly recent articles not yet fully MeSH-indexed.
- **Why:** dominated by **indexing lag**, not wrong content. The filter works as
  intended in exactly one case (a mouse acetaminophen study).

### Tier 3 · + reported PK params

- **Query:** tier 2 **AND** `AUC OR Cmax OR clearance OR "half-life" OR "volume of distribution"[tiab]`
- **Recall:** 76/152 = **50%** · **ALL-PMC:** 21,256 → 42,512 · **OA-subset:** 11,434 → 22,868
- **Dropped vs tier 2: 28 papers.** Titles like "Pharmacokinetics of enalapril in
  normal subjects and patients with renal impairment" are unambiguous PK studies
  whose **parameters live in tables, not the abstract**, so no parameter token
  appears in searchable text.
- **Why:** requiring a parameter keyword trades table-only PK papers away for precision.

### Tier 4 · + dosing / clinical

- **Query:** tier 3 **AND** `"single dose" OR "oral administration" OR "healthy volunteers/subjects" OR "steady state"[tiab]`
- **Recall:** 49/152 = **32%** · **ALL-PMC:** 5,715 → 17,728 · **OA-subset:** 2,707 → 8,397
- **Dropped vs tier 3: 27 papers.** Human PK papers with parameters that describe
  dosing outside the narrow cue list — disease-cohort and special-population studies
  ("Paracetamol elimination in patients with NIDDM", "Caffeine disposition in
  obesity", "Paracetamol metabolism in pregnancy") and IV/other routes.
- **Why:** the cue list is tuned to healthy-volunteer single-dose studies and
  systematically misses **patient-population PK**.

### Cross-tier takeaways

1. The dominant loss is **abstract-vs-full-text mismatch**: PK data reported only in
   tables/figures while the abstract emphasizes PD, metabolism, or assay. No
   abstract-level query can recover these — a **full-text / table-aware search or a
   classifier over full text** is the only fix, and would lift the ceiling above the
   tier-1 estimate.
2. A smaller, correctable loss is **MeSH indexing lag** on recent papers — adding an
   un-indexed-safe branch (e.g. `NOT medline[sb]` OR title/abstract-only human cues)
   would recover most tier-1→2 drops.
3. Narrow parameter/dosing lexicons **systematically drop patient-population and
   table-only PK studies**, biasing the tight tiers toward healthy-volunteer
   pharmacology. Their recall-scaled estimates are therefore lower bounds skewed to
   one study type, not neutral samples.
