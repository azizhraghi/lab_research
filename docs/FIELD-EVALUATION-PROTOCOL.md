# Field evaluation preparation

Real lab data is still to be obtained, as confirmed by the project owner. Software regression fixtures are not scientific evidence.

## Request from the supervisor

For one authorized parcel, request crop and growth stage, area, coordinates, measurement depth, field capacity and wilting point with units and provenance. Request a timestamped series of root-zone water storage, rainfall, reference evapotranspiration, temperature where available, sensor identifier and quality notes. Include every actual irrigation application, its amount, time and method.

Clarify whether the measurements are volumetric percent or millimetres of root-zone storage. Do not convert without a documented measurement depth and representative root-zone assumption. Clarify whether daily rainfall and ET totals precede or follow the soil measurement: applying the same daily balance twice would invalidate the comparison.

Also request one authorized researcher profile and a known publication with DOI/ORCID or other identifiers, plus permission for any public display. These support an independently checked bibliometrics demonstration.

## Acceptance protocol

1. Preserve the raw source, units, dates and permissions. Import only the authorized working copy.
2. Agree expected sampling cadence and the operational freshness limit. Correct gaps, sensor errors and unit mismatches through the reviewed workflow.
3. Use a continuous segment to fit calibration parameters. Reserve a later segment before fitting as a separate evaluation period; do not tune on that later segment.
4. Compare predicted storage against observations on the held-out period. Report sample count, dates, MAE, RMSE, bias, missing values and assumptions. Compare with a simple agreed baseline such as persistence of the last observation.
5. Ask a domain supervisor to review the direction and magnitude of recommended irrigation. Software approval logs are not agronomic approval of the model itself.
6. Report limitations: parcel-level model, assumed coefficients, forecast uncertainty, sensor representativeness, parameter identifiability and lack of field actuation.

There is no built-in independent-validation report yet. The application's displayed Fit RMSE is in-sample. A held-out evaluation must be implemented or calculated separately with traceable inputs before claiming model validation. A single test case cannot justify water savings or general predictive accuracy.

## Submission evidence

Package the agreed reduced scope, architecture, source revision, repeatable installation commands, regression results, a short workflow demonstration, and the completed field evaluation if data becomes available. If it does not, explicitly submit a software prototype with a future field-evaluation protocol. Do not fill missing scientific evidence with invented data.
