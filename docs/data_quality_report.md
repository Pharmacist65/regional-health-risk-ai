# Data Quality Report

## Purpose

This report summarises whether the aggregate demo inputs meet the project's expected schemas and basic quality rules before scoring.

It is a portfolio and public-health planning artefact only. It is not clinical validation, model validation or evidence that the synthetic data represents real local need.

## Current synthetic dataset snapshot

| Dataset | Rows | Columns | Areas | Missing values | Blank values | Duplicate key rows | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Aggregate prescribing | 384 | 6 | 8 | 0 | 0 | 0 | Pass |
| Public-health indicators | 8 | 9 | 8 | 0 | 0 | 0 | Pass |

## Checks

The quality report is generated from `src/quality_report.py` and uses the validation rules in `src/validation.py`.

It covers:

- required columns
- missing and blank values
- duplicate aggregate keys
- parseable prescribing month values
- supported medication-class labels
- non-negative aggregate prescribing rates
- valid latitude and longitude ranges
- public-health percentage and index ranges from 0 to 100

## Interpretation limits

Passing these checks only means the demo data can move through the current analytics pipeline without obvious schema or quality failures.

It does not mean:

- the synthetic values are real
- the score is clinically validated
- an area has a real disease burden
- an intervention is clinically indicated
- the system is suitable for individual decisions

Before any real aggregate open-data use, the same report should be paired with documented source provenance, extract dates, licence review, bias review and stakeholder governance.
