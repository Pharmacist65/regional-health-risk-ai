# Data governance

## Purpose

This project is a portfolio demonstration of aggregate public-health analytics. The default runtime path uses synthetic area-level data only.

## Data boundary

Allowed:

- synthetic aggregate prescribing indicators
- synthetic aggregate public-health indicators
- optional local aggregate open-data CSVs with documented provenance

Not allowed:

- patient-level records
- simulated identifiable patient records
- private prescribing extracts
- API keys, tokens or credentials
- outputs framed as clinical advice or individual risk prediction

## Validation checks

`src/validation.py` performs lightweight input checks before connector data enters the scoring pipeline.

Prescribing checks:

- required columns
- parseable month values
- missing or blank area identifiers
- duplicate rows by month, area and medication class
- unsupported medication classes
- non-numeric or negative item and cost rates

Public-health checks:

- required columns
- missing or blank area identifiers
- duplicate rows by area code
- non-numeric values
- latitude and longitude ranges
- percentage and index ranges from 0 to 100

## Real aggregate data readiness

Before any real open-data use, the project would need:

- source licence review
- documented extract date and refresh cadence
- column mapping from source data into the project schema
- data-quality report for missingness, duplicates and outliers
- review of whether the selected indicators are suitable for the intended public-health planning question
- governance review before any deployment outside a portfolio demo

## Interpretation limits

Validation makes the input safer to process, but it does not make the score clinically valid. The dashboard remains a prevention-prioritisation analytics demo, not a clinical system.
