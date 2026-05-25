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

## Local open-data mapping

`src/open_data_mapping.py` provides optional helpers for local downloaded aggregate CSVs:

- `map_openprescribing_aggregate_csv(...)` maps OpenPrescribing-style prescribing extracts into the internal aggregate prescribing schema.
- `map_ohid_fingertips_indicator_csv(...)` maps OHID/Fingertips-style long indicator exports into the internal public-health schema.

The mapping layer is offline-only. It accepts local files or in-memory dataframes, applies explicit column and indicator mappings where needed, and then runs the same validation checks listed above. It does not make live API calls, require API keys or change the default synthetic-data runtime path.

## Data quality report

`src/quality_report.py` converts validation results into a compact, dashboard-friendly summary. It reports row counts, column counts, area counts, missing values, blank values, duplicate aggregate keys and validation issues for each input dataset.

The Streamlit dashboard surfaces this in the method and governance tab as a data-quality snapshot. The static documentation version is available in [data_quality_report.md](data_quality_report.md).

This report is a schema and quality guardrail only. It does not validate the score clinically, verify real-world representativeness or support individual decisions.

## Real aggregate data readiness

Before any real open-data use, the project would need:

- source licence review
- documented extract date and refresh cadence
- column mapping from source data into the project schema
- saved mapping assumptions for medication classes and public-health indicators
- data-quality report for missingness, duplicates and outliers
- review of whether the selected indicators are suitable for the intended public-health planning question
- governance review before any deployment outside a portfolio demo

## Interpretation limits

Validation makes the input safer to process, but it does not make the score clinically valid. The dashboard remains a prevention-prioritisation analytics demo, not a clinical system.
