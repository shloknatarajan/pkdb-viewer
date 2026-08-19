# PK-DB Curation and Analysis Flow

PK-DB combines human interpretation of pharmacokinetics publications with an
automatic non-compartmental analysis (NCA). The automatic calculation starts
only after a curator has converted the source publication into structured,
validated data.

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
Calculated PK parameters stored alongside reported parameters
        |
        v
Human review and second-curator quality check
```

## Human Curation

The curator reconstructs the meaning of the experiment from the paper. This
includes:

- identifying groups and individuals and recording characteristics such as
  species, sex, age, body weight, and health status;
- encoding interventions, including substance, dose, route, formulation, and
  timing;
- transcribing numerical values from tables and supplementary files;
- digitizing concentration-time points from graphs when raw values are not
  published;
- associating each curve with the correct substance, tissue, intervention, and
  group or individual;
- distinguishing values, means, medians, SDs, and SEs; and
- mapping terminology and units to PK-DB's standardized concepts.

This is not merely data entry. A human must determine what each plotted line,
table column, unit, and experimental arm represents. PK-DB does not infer this
context directly from the PDF.

## Automatic Analysis

Once a concentration-time series is structured, PK-DB calculates parameters
using NCA rather than fitting a compartment or PBPK model:

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

## Provenance and Limitations

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
