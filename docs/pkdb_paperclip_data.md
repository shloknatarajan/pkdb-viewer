# PK-DB and Paperclip Dataset Overview

Counts were checked on **2026-08-19**. PK-DB's canonical website is
[pk-db.com](https://pk-db.com/); the live study count below comes from its public
[`studies` API](https://pk-db.com/api/v1/studies/?format=json&page_size=1).

| Measure | Count | Meaning |
|---|---:|---|
| Publicly listed studies currently in PK-DB | **803** | Count returned by the live `studies` endpoint. A study normally represents one publication or trial. |
| Studies available in the historical GitHub download | **661** | Studies in the PK-DB maintainers' 2021-12-03 CSV snapshot. This is the downloadable dataset used here because the anonymous live API does not return the measurement data reliably. |
| Current PK-DB studies mapped to a PMCID | **155** | PMCID mappings in the repository's live-API metadata snapshot (`pkdb-api/summary.json`). |
| Open/downloadable comparison papers with a PMCID | **33** | The comparison cohort in `pkdb-api/open_access_pmcids.txt`. This is the denominator for the Paperclip overlap below, not all 803 live studies. |
| Comparison papers readable with Paperclip `cat` | **2 of 33** | **6.1%** of this PMCID cohort: `PMC3043256` and `PMC4411542`. |
| Comparison papers not readable with Paperclip `cat` | **31 of 33** | `paperclip lookup pmc <PMCID>` returned no document, so no Paperclip paper path was available to `cat`. |

## PK-DB curation flow

Human analysis is concentrated at the start of both flows: curators reconstruct
the study design, connect results to the correct subjects and interventions,
and preserve statistical and unit context. Automatic PK analysis occurs only
when concentration-time points are available.

### Scale of the live database

PK-DB's live [`statistics` endpoint](https://pk-db.com/api/v1/statistics/?format=json)
reports the following totals for version 0.9.8. Averages use the endpoint's own
denominator of 819 studies, so they are internally consistent and represent an
average per PK-DB study (normally one paper or trial).

| Record type | Total | Average per study |
|---|---:|---:|
| Scalar outputs | **138,411** | **169.00** |
| Calculated scalar outputs | **25,967** | **31.71** |
| Concentration or other timecourses | **6,103** | **7.45** |
| Scatter records | **164** | **0.20** |
| All measurement records above | **144,678** | **176.65** |

"Calculated scalar outputs" are a subset of all outputs, not an additional
record category, so the combined measurement total counts outputs,
timecourses, and scatters only. A timecourse is one series containing multiple
time-value points; 6,103 is not the number of individual coordinates.

The statistics endpoint reports 819 studies while the paginated public
`studies` endpoint currently returns 803. Because the endpoints expose
different totals, this document uses 819 only for the averages in this table
and retains 803 for the publicly listed study count above.

### Papers with concentration-time data

```text
Paper or source dataset
        |
        v
Human curation and graph digitization
        |
        v
Structured study, intervention, and concentration-time data
        |
        v
Validation, ontology mapping, and unit normalization
        |
        v
Automatic non-compartmental analysis
        |
        v
Calculated parameters stored alongside reported parameters
        |
        v
Human review and second-curator quality check
```

Curators transcribe tabled timepoints or digitize graph coordinates and assign
each series to its substance, tissue, dose, intervention, and subject group.
PK-DB can then derive parameters such as AUC, Cmax, Tmax, half-life, clearance,
and volume of distribution using non-compartmental analysis.

### Papers without concentration-time data

```text
Paper
  |
  v
Human extraction of study design and reported scalar parameters
  |
  v
Unit normalization, ontology mapping, and validation
  |
  v
Reported outputs stored in PK-DB
  |
  v
Human review and second-curator quality check
```

When only scalar parameters are published, curators transcribe the authors'
values and statistical context. PK-DB standardizes their representation but
cannot reproduce the original calculation without the underlying timecourse.

The two flows and calculation details are documented further in
[`PKDB_ANALYSIS_FLOW.md`](PKDB_ANALYSIS_FLOW.md).

## Why 803 is not the downloadable total

The live site reports 803 studies, but the usable downloadable release is an
older snapshot containing 661 studies. The project uses the historical
[`testdata_concise_false.zip`](https://github.com/matthiaskoenig/pkdb_analysis/blob/develop/tests/data/testdata_concise_false.zip)
from `matthiaskoenig/pkdb_analysis` because anonymous calls to the live PK-DB API
return relational study information but return no outputs and expose no usable
timecourse or scatter endpoints. Those measurements are essential to the
project. The artifact contains eight CSV tables and is dated 2021-12-03. See
[`PKDB_DOWNLOAD_INFORMATION.md`](PKDB_DOWNLOAD_INFORMATION.md) for the endpoint
checks and complete provenance.

The 155 PMCID count describes the current 803-study metadata snapshot. The
Paperclip comparison is deliberately narrower: it uses the 33 PMCID-bearing
papers selected by the repository's open/downloadable workflow. Each of those
33 identifiers was checked against the live Paperclip CLI on 2026-08-19. These
counts must not be substituted for one another.

## Concentration curves and directly reported PK parameters

The local viewer currently contains **55 downloaded PK-DB paper records** in
`app_data/pkdb_annotations/`. The following counts use those 55 records as the
denominator:

| Paper content | Count | Percentage |
|---|---:|---:|
| Concentration-time curve graphs | **42 of 55** | **76.4%** |
| Author-reported standard PK parameters in tables or text | **35 of 55** | **63.6%** |
| Both curves and directly reported standard PK parameters | **28 of 55** | **50.9%** |

Among the 42 papers with concentration-time curves, **28 (66.7%)** also report
standard PK parameters numerically without requiring graph reading. The other
**14 (33.3%)** have curves but no author-reported standard parameter values in
the PK-DB extraction; their standard parameters, when present, were calculated
from the digitized curves.

For this comparison, "standard PK parameters" means AUC, Cmax, Tmax,
elimination rate or half-life, clearance, and volume of distribution. A value
was counted as directly reported when the raw PK-DB output has
`calculated=False`, meaning it was reported by the paper's authors and
transcribed by a curator. Outputs with `calculated=True` were derived by
PK-DB's pharmacokinetics pipeline from concentration-time curves. If the
definition is broadened to any author-reported scalar PK-related result,
including concentrations, recovery, secretion rates, and metabolic ratios,
all 55 records contain at least one; that broader count is not equivalent to
having a conventional summary PK parameter table.

The curve count is based on the presence of PK-DB timecourse records. In this
snapshot, those timecourses were digitized from paper figures rather than
transcribed from tables. Only 16 of the 42 curve-bearing records have locally
readable full text: figure-based curves were visually confirmed in 15, while
one abstract-only scan was undetermined. The remaining 26 are represented
locally by abstracts, so their classification relies on PK-DB's extraction
provenance rather than a new visual inspection of each paper.

## Papers readable through Paperclip `cat`

Two of the 33 comparison papers resolve to a Paperclip document and expose
`meta.json` and `content.lines`:

```text
PMC3043256
PMC4411542
```

## Papers not readable through Paperclip `cat`

For the other 31 identifiers, `paperclip lookup pmc <PMCID>` returned
`No documents found`. Because lookup returned no Paperclip document path, a
subsequent `cat /papers/<PMCID>/content.lines` is not available.

This is a Paperclip coverage gap rather than a full-text availability gap.
Europe PMC provides free HTML and PDF pages for all 31 identifiers. Thirty map
to studies in the local viewer: six already had machine-readable full text and
the other 24 now have `paper.md` files generated from the PDFs' embedded text
layers. All 24 PDFs yielded substantial text without OCR; original scanned page
images remain linked where they were previously available. `PMC1430174` is the
only comparison paper without a corresponding local viewer study directory.

Free access does not imply an open reuse licence. Europe PMC marks all 31 as
outside its open-access subset, so the generated Markdown retains source links
and does not assign a licence that the source does not report.

```text
PMC1368322  PMC1368325  PMC1368572  PMC1368573
PMC1380033  PMC1380034  PMC1380095  PMC1381556
PMC1400629  PMC1401099  PMC1401868  PMC1428054
PMC1428091  PMC1429435  PMC1430174  PMC1463596
PMC1463861  PMC172463   PMC1884944  PMC245075
PMC2561102  PMC2675050  PMC2810805  PMC2824477
PMC370948   PMC372111   PMC3775655  PMC423314
PMC424555   PMC4383763  PMC5299073
```

## Paperclip `cat` results

### `PMC3043256`

- **Paperclip path:** `/papers/PMC3043256/content.lines`
- **Title:** *Marginal increase of sunitinib exposure by grapefruit juice*
- **Journal/year:** *Cancer Chemotherapy and Pharmacology* (2010)
- **Identifiers:** PMID 20512335; DOI 10.1007/s00280-010-1367-0
- **Paperclip content:** 133 numbered lines, including the article body,
  figures, references, acknowledgments, and licence statement.

Paperclip reports a pharmacokinetic study of eight cancer patients receiving
sunitinib. Patients consumed grapefruit juice before the second PK assessment,
and midazolam was used as a CYP3A4 probe. Grapefruit juice increased relative
sunitinib bioavailability by 11% and mean midazolam exposure by approximately
50%. The authors considered the sunitinib increase statistically significant
but not clinically relevant. [1]

Commands used:

```bash
paperclip cat /papers/PMC3043256/meta.json
paperclip cat /papers/PMC3043256/content.lines
```

### `PMC4411542`

- **Paperclip path:** `/papers/PMC4411542/content.lines`
- **Title:** *The Insulin Resistance but Not the Insulin Secretion Parameters
  Have Changed in the Korean Population during the Last Decade*
- **Journal/year:** *Diabetes & Metabolism Journal* (2015)
- **Identifiers:** PMID 25922805; DOI 10.4093/dmj.2015.39.2.117
- **Paperclip content:** 91 numbered lines, including the article body,
  figures, references, and acknowledgments.

Paperclip reports a comparison of 578 Korean subjects studied in 1997–1999 and
504 studied in 2007–2011 using 75-g oral glucose tolerance tests. The later
cohort showed greater insulin resistance and lower insulin sensitivity, while
the insulinogenic index did not differ significantly. The authors concluded
that insulin resistance had worsened while insulin secretory function remained
unchanged, but warned that the tertiary-hospital cohort could introduce
selection bias. [2]

Commands used:

```bash
paperclip cat /papers/PMC4411542/meta.json
paperclip cat /papers/PMC4411542/content.lines
```

## Sources and reproducibility

- Live PK-DB total: [PK-DB public studies API](https://pk-db.com/api/v1/studies/?format=json&page_size=1), checked 2026-08-19.
- Downloadable snapshot: `PKDB_DOWNLOAD_INFORMATION.md` and the
  [`pkdb_analysis` GitHub artifact](https://github.com/matthiaskoenig/pkdb_analysis/blob/develop/tests/data/testdata_concise_false.zip).
- Current PMCID mappings: `pkdb-api/summary.json` and
  `pkdb-api/pmid_to_pmcid.csv`.
- Comparison cohort: `../pkdb-api/open_access_pmcids.txt` (33 unique PMCIDs).
- Local PK-DB PMCID files: `../pkdb-api/pkdb_pmcids.txt` (32 unique PMCIDs) and
  `../pkdb-api/open_access_pmcids.txt` (33 unique PMCIDs). These files were not treated as
  proof of live Paperclip availability.
- Live Paperclip availability: `paperclip lookup pmc <PMCID>` followed by
  `paperclip cat /papers/<PMCID>/meta.json` and `content.lines` when lookup
  succeeded, checked 2026-08-19.

The local-file overlap can be reproduced with the following commands, but it
must be followed by the live Paperclip lookup/`cat` checks described above:

```bash
comm -12 <(sort -u pkdb-api/open_access_pmcids.txt) <(sort -u pkdb-api/pkdb_pmcids.txt)
comm -23 <(sort -u pkdb-api/open_access_pmcids.txt) <(sort -u pkdb-api/pkdb_pmcids.txt)
```

--------
REFERENCES

[1] van Erp NP, et al. "Marginal increase of sunitinib exposure by grapefruit
    juice." *Cancer Chemotherapy and Pharmacology* (2010).
    https://paperclip.gxl.ai/citations/papers/PMC3043256#L12-L16

[2] Yang HK, et al. "The Insulin Resistance but Not the Insulin Secretion
    Parameters Have Changed in the Korean Population during the Last Decade."
    *Diabetes & Metabolism Journal* (2015).
    https://paperclip.gxl.ai/citations/papers/PMC4411542#L15-L17
