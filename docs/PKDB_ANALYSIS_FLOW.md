# PK-DB Curation and Analysis Flow

PK-DB combines human interpretation of pharmacokinetics publications with
structured validation and, when concentration-time data are available,
automatic non-compartmental analysis (NCA). Papers follow one of two flows.

## 1. Papers With Concentration-Time Data

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

A curator transcribes timepoints from tables or digitizes them from graphs,
then associates each curve with the correct substance, tissue, intervention,
and group or individual. The curator must interpret plotted lines, units,
experimental arms, dosing times, and whether values represent individuals,
means, medians, SDs, or SEs. PK-DB does not infer this context from the PDF.

Once the series is structured, PK-DB uses NCA rather than fitting a compartment
or PBPK model:

- `Cmax` is the largest observed concentration and `Tmax` is its time relative
  to dosing.
- `AUC0-last` is calculated with the linear trapezoidal rule.
- The terminal elimination slope is fitted by linear regression of `ln(C)`
  against time using observations after `Cmax`.
- `kel` is the negative terminal slope and `t1/2 = ln(2) / kel`.
- `AUC0-inf = AUC0-last + Clast / kel`.
- With a known dose, `CL = Dose / AUC0-inf` and
  `Vd = Dose / (AUC0-inf * kel)`.

The implementation validates dimensionality and warns when, for example, fewer
than three post-peak points are available, the fitted terminal slope is
positive, or the extrapolated AUC is large.

## 2. Papers Without Concentration-Time Data

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

Many papers publish only scalar parameters such as AUC, clearance, `Cmax`,
`Tmax`, half-life, volume of distribution, or bioavailability. The curator
transcribes these values and their statistical context, then links them to the
correct subjects, substance, tissue, dose, and intervention.

PK-DB cannot run NCA without the underlying time and concentration points.
These values are therefore stored as **reported parameters**: they were
calculated by the paper's authors using methods and raw data that may not be
available to PK-DB. The database can normalize and validate their representation
but cannot independently reproduce the calculation.

If a paper contains neither timecourses nor scalar PK parameters, it may still
contribute study metadata or other experimental outputs, but it provides little
material for PK parameter analysis.

## Shared Provenance and Limitations

Parameters reported by the paper and parameters calculated by PK-DB are
separate provenance categories and should not be conflated. Calculations from a
published group-mean curve can differ from the mean of parameters calculated
for individual subjects. The automatic terminal-phase rule also uses all
post-`Cmax` observations; it does not reproduce expert selection of a terminal
log-linear interval for every curve.

## References

- [PK-DB publication and curation workflow](https://pmc.ncbi.nlm.nih.gov/articles/PMC7779054/)
- [PK-DB analysis implementation](https://github.com/matthiaskoenig/pkdb_analysis)
- [PK-DB website](https://pk-db.com/)
