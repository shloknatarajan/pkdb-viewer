# PK-DB Evidence Schema

## Purpose

This document defines a relational schema and analytical tuple for representing
the pharmacokinetic evidence in this repository.

The central design goal is to make one database row correspond to a useful,
well-scoped scientific fact without losing its publication, subject,
intervention, measurement, unit, or provenance context.

PK-DB is not naturally a flat table of `(drug, parameter, value)` rows. A result
only becomes interpretable when it is connected to:

- the study or publication from which it came;
- the group or individual on which it was measured;
- every intervention applied to that subject;
- the measured analyte and biological tissue;
- the endpoint or measurement type;
- the statistic, value, uncertainty, and unit;
- the analytical method and reported/calculated provenance.

## Recommended row grain

The recommended analytical row is:

> One estimate of one endpoint, for one analyte and biological matrix, measured
> in one subject context under one set of interventions.

Expressed as a tuple:

```text
(
  study_id,
  subject_id,
  intervention_set_id,
  analyte_id,
  tissue_id,
  endpoint_id,
  result_kind,
  time,
  statistic,
  value,
  unit,
  uncertainty_type,
  uncertainty_value,
  method_id,
  provenance
)
```

### Concrete example

```text
(
  "PKDB00024",          -- study
  "group:143",          -- ten healthy volunteers
  "{intervention:218}", -- 1.5 g oral paracetamol
  "apap",               -- measured analyte: paracetamol
  "plasma",
  "thalf",              -- elimination half-life
  "scalar",
  null,
  "mean",
  3.4,
  "hour",
  "SD",
  0.3,
  null,
  "reported"
)
```

After joining the subject and intervention dimensions, this means:

> In ten healthy, nonsmoking volunteers aged 21–32 years, a 1.5 g oral
> paracetamol dose was associated with a mean plasma elimination half-life of
> 3.4 ± 0.3 hours.

Source: `app_data/pkdb_annotations/PKDB00024/study.json`, output `pk=7255`, group
`pk=143`, and intervention `pk=218`.

## Novel-information signature

For estimating how many distinct scientific contexts are present, use:

```text
(
  study_id,
  subject_id,
  intervention_set,
  analyte_id,
  tissue_id,
  endpoint_id,
  result_kind
)
```

The numeric result is deliberately excluded from this key. Including the value
would make every different measurement trivially “novel.”

The study remains in the key because the same protocol reported by two
independent studies is replication, not duplication.

### Snapshot coverage expressed as tuples

The following figures were calculated from the 55 studies in
`app_data/pkdb_annotations/index.json`:

```python
coverage_counts = [
    ("studies", 55),
    ("subject_entities", 1_237),          # 144 groups + 1,093 individuals
    ("unique_characteristic_facts", 1_784),
    ("characteristic_types", 36),
    ("interventions", 161),
    ("administered_substances", 37),
    ("measured_substances", 70),
    ("tissues", 5),
    ("endpoint_types", 37),

    ("scalar_experimental_contexts", 5_007),
    ("unique_scalar_observations", 11_584),
    ("observation_intervention_links", 19_494),

    ("timecourse_contexts", 267),
    ("timecourse_series", 453),
    ("timecourse_points", 6_176),

    ("scatter_series", 7),
    ("scatter_point_pairs", 184),
]
```

This yields approximately **5,281 distinct evidence contexts**:

- 5,007 scalar contexts;
- 267 time-course contexts;
- 7 scatter datasets.

Within those contexts are 11,584 unique scalar observations and 6,176 usable
time-course points.

## Why 19,494 output rows are not 19,494 measurements

The checked-in JSON contains 19,494 entries in its combined `outputs` arrays,
but only 11,584 unique `(study_id, output.pk)` identifiers.

The difference is primarily caused by flattening many-to-many intervention
relationships. For example, output `169820` in `PKDB00248` is the same measured
midazolam bioavailability value (`0.005`, dimensionless) associated with two
interventions:

```text
(output 169820, intervention 3189: oral midazolam)
(output 169820, intervention 3192: rifampicin)
```

The normalized representation should be one observation plus two relationship
rows:

```text
observation
-----------
169820 | midazolam | bioavailability | median | 0.005 | dimensionless

observation_intervention
------------------------
169820 | 3189 | primary dose
169820 | 3192 | co-treatment
```

It should not duplicate the measurement itself.

## Normalized relational schema

The definitions below are logical schemas. Types such as `ontology_id` and
`unit_id` should reference controlled vocabulary tables rather than storing
unvalidated text.

### Study and provenance

```sql
CREATE TABLE study (
  study_id            TEXT PRIMARY KEY,
  reference_id        BIGINT,
  name                TEXT NOT NULL,
  title               TEXT,
  publication_date    DATE,
  pmid                 TEXT,
  doi                  TEXT,
  journal              TEXT,
  source_identifier    TEXT,
  license              TEXT,
  snapshot_id          TEXT NOT NULL,
  curator_notes        TEXT
);
```

A study normally represents one publication or clinical trial and is the root
provenance object for all subject, intervention, and measurement data.

### Substance vocabulary

```sql
CREATE TABLE substance (
  substance_id        TEXT PRIMARY KEY,
  preferred_label     TEXT NOT NULL,
  ontology_source     TEXT,
  ontology_accession  TEXT,
  molecular_weight    NUMERIC,
  metadata            JSONB NOT NULL DEFAULT '{}'
);
```

“Substance” is broader than “drug.” It can represent an administered drug,
metabolite, endogenous biomarker, food product, challenge substance, or control.

### Groups and individuals

```sql
CREATE TYPE subject_kind AS ENUM ('group', 'individual');

CREATE TABLE subject_entity (
  subject_id           BIGINT PRIMARY KEY,
  study_id             TEXT NOT NULL REFERENCES study(study_id),
  kind                 subject_kind NOT NULL,
  parent_group_id      BIGINT REFERENCES subject_entity(subject_id),
  name                 TEXT NOT NULL,
  reported_count       INTEGER,
  source_pk            BIGINT,
  UNIQUE (study_id, source_pk)
);
```

`reported_count` is meaningful for groups but must not be summed blindly.
Parent/child groups, overlapping strata, and crossover periods can describe the
same participants more than once.

### Subject characteristics

```sql
CREATE TABLE subject_characteristic (
  characteristic_id   BIGINT PRIMARY KEY,
  subject_id           BIGINT NOT NULL REFERENCES subject_entity(subject_id),
  characteristic_type_id TEXT NOT NULL,
  choice_id            TEXT,
  substance_id         TEXT REFERENCES substance(substance_id),
  value                NUMERIC,
  mean                 NUMERIC,
  median               NUMERIC,
  minimum              NUMERIC,
  maximum              NUMERIC,
  sd                   NUMERIC,
  se                   NUMERIC,
  cv                   NUMERIC,
  unit_id              TEXT,
  reported_count       INTEGER,
  missing_reason       TEXT,
  reported_value_text  TEXT,
  reported_unit_text   TEXT
);
```

The flexible characteristic table is intentional. PK-DB populations can be
described by age, sex, body weight, disease, smoking, ethnicity, genotype,
medication, fasting, renal function, and study-specific characteristics.

The reported representation and normalized value should both be retained.
Normalization must not overwrite the source value.

### Interventions

```sql
CREATE TABLE intervention (
  intervention_id      BIGINT PRIMARY KEY,
  study_id             TEXT NOT NULL REFERENCES study(study_id),
  name                 TEXT NOT NULL,
  substance_id         TEXT REFERENCES substance(substance_id),
  intervention_type_id TEXT,
  route_id             TEXT,
  form_id              TEXT,
  application_type_id  TEXT,
  dose_value           NUMERIC,
  dose_mean            NUMERIC,
  dose_median          NUMERIC,
  dose_minimum         NUMERIC,
  dose_maximum         NUMERIC,
  dose_sd              NUMERIC,
  dose_se              NUMERIC,
  dose_cv              NUMERIC,
  dose_unit_id         TEXT,
  start_time           NUMERIC,
  end_time             NUMERIC,
  time_unit_id         TEXT,
  missing_reason       TEXT,
  reported_dose_text   TEXT,
  reported_unit_text   TEXT
);
```

An intervention can be a dose, infusion, co-medication, dietary exposure,
fasting condition, or other experimental change. The substance is nullable
because not every intervention is a drug administration and some sources do not
report it.

### Common observation context

```sql
CREATE TYPE result_kind AS ENUM ('scalar', 'timecourse', 'scatter');
CREATE TYPE provenance_kind AS ENUM ('reported', 'calculated', 'inferred');

CREATE TABLE observation (
  observation_id       BIGINT PRIMARY KEY,
  study_id             TEXT NOT NULL REFERENCES study(study_id),
  subject_id           BIGINT NOT NULL REFERENCES subject_entity(subject_id),
  analyte_id           TEXT REFERENCES substance(substance_id),
  tissue_id            TEXT,
  endpoint_id          TEXT NOT NULL,
  method_id            TEXT,
  kind                 result_kind NOT NULL,
  provenance           provenance_kind NOT NULL,
  label                TEXT,
  source_pk            BIGINT,
  UNIQUE (study_id, source_pk, kind)
);
```

### Observation–intervention relationship

```sql
CREATE TYPE intervention_role AS ENUM (
  'primary',
  'co_treatment',
  'pre_treatment',
  'condition',
  'unspecified'
);

CREATE TABLE observation_intervention (
  observation_id       BIGINT NOT NULL REFERENCES observation(observation_id),
  intervention_id      BIGINT NOT NULL REFERENCES intervention(intervention_id),
  role                 intervention_role NOT NULL DEFAULT 'unspecified',
  PRIMARY KEY (observation_id, intervention_id)
);
```

This join table is essential. One result can depend on several interventions,
and duplicating the observation for every intervention inflates measurement
counts.

### Scalar results

```sql
CREATE TABLE scalar_result (
  observation_id       BIGINT PRIMARY KEY REFERENCES observation(observation_id),
  observation_time     NUMERIC,
  time_unit_id         TEXT,
  statistic_type       TEXT,
  value                NUMERIC,
  mean                 NUMERIC,
  median               NUMERIC,
  minimum              NUMERIC,
  maximum              NUMERIC,
  sd                   NUMERIC,
  se                   NUMERIC,
  cv                   NUMERIC,
  choice_id            TEXT,
  unit_id              TEXT,
  reported_value_text  TEXT,
  reported_unit_text   TEXT,
  missing_reason       TEXT
);
```

The wide statistic fields mirror the source representation and keep a mean,
range, and experimental error together as one reported estimate. A more fully
normalized implementation could instead store each statistic in an
`observation_statistic` child table.

### Time-course series and points

```sql
CREATE TABLE timecourse_series (
  observation_id       BIGINT PRIMARY KEY REFERENCES observation(observation_id),
  series_name          TEXT
);

CREATE TABLE timecourse_point (
  observation_id       BIGINT NOT NULL REFERENCES timecourse_series(observation_id),
  point_index          INTEGER NOT NULL,
  time                 NUMERIC NOT NULL,
  time_unit_id         TEXT NOT NULL,
  value                NUMERIC,
  mean                 NUMERIC,
  sd                   NUMERIC,
  value_unit_id        TEXT,
  PRIMARY KEY (observation_id, point_index)
);
```

One `timecourse_point` row corresponds to one position on a curve. Array order
is preserved with `point_index`, including repeated time values if they were
reported.

Example:

```text
(
  observation="PKDB00427:1255",
  point_index=5,
  time=1.3830119,
  time_unit="hour",
  value=0.0052923703,
  value_unit="gram/liter"
)
```

### Scatter series and point pairs

```sql
CREATE TABLE scatter_series (
  scatter_id           BIGINT PRIMARY KEY,
  study_id             TEXT NOT NULL REFERENCES study(study_id),
  name                 TEXT,
  x_endpoint_id        TEXT NOT NULL,
  x_substance_id       TEXT REFERENCES substance(substance_id),
  x_tissue_id          TEXT,
  x_unit_id            TEXT,
  y_endpoint_id        TEXT NOT NULL,
  y_substance_id       TEXT REFERENCES substance(substance_id),
  y_tissue_id          TEXT,
  y_unit_id            TEXT
);

CREATE TABLE scatter_point (
  scatter_id           BIGINT NOT NULL REFERENCES scatter_series(scatter_id),
  point_index          INTEGER NOT NULL,
  x_value              NUMERIC NOT NULL,
  y_value              NUMERIC NOT NULL,
  PRIMARY KEY (scatter_id, point_index)
);
```

Scatters remain separate because they represent a relationship between two
measured axes rather than one endpoint over time.

### Controlled vocabulary and units

```sql
CREATE TABLE ontology_concept (
  concept_id           TEXT PRIMARY KEY,
  concept_kind         TEXT NOT NULL,
  preferred_label      TEXT NOT NULL,
  description          TEXT,
  synonyms             TEXT[],
  ontology_source      TEXT,
  ontology_accession   TEXT,
  metadata             JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE unit (
  unit_id              TEXT PRIMARY KEY,
  display_label        TEXT NOT NULL,
  canonical_expression TEXT NOT NULL,
  dimensionality       TEXT,
  metadata             JSONB NOT NULL DEFAULT '{}'
);
```

Endpoint, tissue, route, form, application, characteristic, choice, method, and
other categorical identifiers should reference controlled ontology concepts.

## Analytical evidence view

The normalized schema should be accompanied by a denormalized view for data
analysis and export:

```sql
CREATE VIEW pk_evidence AS
SELECT
  o.study_id,
  o.observation_id,
  o.subject_id,
  s.kind AS subject_kind,
  s.name AS subject_name,
  o.analyte_id,
  o.tissue_id,
  o.endpoint_id,
  o.kind AS result_kind,
  sr.observation_time,
  sr.time_unit_id,
  sr.statistic_type,
  COALESCE(sr.value, sr.mean, sr.median) AS estimate,
  sr.unit_id,
  sr.sd,
  sr.se,
  sr.cv,
  o.method_id,
  o.provenance
FROM observation o
JOIN subject_entity s ON s.subject_id = o.subject_id
LEFT JOIN scalar_result sr ON sr.observation_id = o.observation_id;
```

Interventions should be exposed as either:

- a separate `pk_evidence_intervention` view with one row per
  observation–intervention link; or
- an ordered JSON/array field when producing a single-row analytical export.

They should not be joined directly into `pk_evidence` without aggregation,
because doing so would duplicate observations that have multiple interventions.

## Suggested export tuple

For CSV, Parquet, or dataframe consumers, use the following human-readable
fields:

```text
study_id
publication
subject_id
subject_kind
population_summary
intervention_set
administered_substances
analyte
tissue
endpoint
result_kind
time
statistic
value
unit
variability
method
provenance
```

This provides “one row = one PK fact” for analysis while retaining the
normalized relational representation underneath.

## Counting rules

When reporting database size, publish all of the following rather than a single
ambiguous “row count”:

1. **Experimental contexts** — distinct novelty signatures.
2. **Observation entities** — distinct `(study_id, source_pk)` measurements.
3. **Observation–intervention links** — the size of the many-to-many relation.
4. **Time-course series and points** — curves and their atomic observations.
5. **Scatter series and pairs** — correlations and their point pairs.
6. **Subject entities and characteristic facts** — population metadata.
7. **Controlled concepts** — substances, endpoints, tissues, routes, and other
   ontology dimensions.

These counts answer different questions and should not be added together as if
they had the same grain.

## Design constraints

- Preserve reported values and units alongside normalized values and units.
- Preserve explicit “not reported” states; do not infer missing values.
- Keep study and source identifiers on every scientific fact.
- Separate reported parameters from parameters calculated by PK-DB.
- Model group and individual results without treating entity counts as a
  deduplicated participant census.
- Support multiple interventions per observation.
- Keep time-course and scatter point ordering stable.
- Use ontology identifiers for substances, endpoints, tissues, routes, forms,
  methods, and subject characteristics.
- Store curator notes and validation warnings without converting them into
  scientific values.

## Repository sources

- `app_data/pkdb_annotations/index.json`
- `app_data/pkdb_annotations/*/study.json`
- `pkdb-api/studies_full.json`
- `src/types.ts`
- `docs/PKDB_ANALYSIS_FLOW.md`
- Grzegorzewski et al., *PK-DB: pharmacokinetics database for individualized
  and stratified computational modeling*, Nucleic Acids Research 49(D1),
  D1358–D1364, DOI: `10.1093/nar/gkaa990`.
