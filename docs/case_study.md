# Case Study

## Summary

Regional Preventive Health Analytics is a privacy-first healthtech portfolio MVP. It demonstrates how synthetic aggregate prescribing indicators and synthetic public-health indicators can be transformed into transparent regional prevention-prioritisation signals.

The project is designed to show product judgement as much as code: it keeps the data boundary safe, avoids clinical decision-support claims and makes the scoring assumptions visible.

Live demo: [Regional Preventive Health Analytics](https://regional-health-risk-ai-ikqhu3ynfpabw2emgxg6br.streamlit.app/)

## Problem

Public-health, pharmacy and primary-care teams often need to compare regional patterns before deciding where further review, awareness material or service-planning effort may be useful. Those workflows need interpretable aggregate signals, not patient-level predictions.

The portfolio challenge was to build a credible MVP that demonstrates this workflow without using private data or implying clinical authority.

## Constraints

- No patient-level data.
- No identifiable synthetic patients.
- No diagnosis, triage, treatment, dosing, prescribing or supplement advice.
- No NHS affiliation, endorsement or approval claim.
- Synthetic aggregate data must remain the default runtime path.
- The app must be runnable by a reviewer without secrets, API keys or private datasets.

## Product Decisions

### Use synthetic aggregate data by default

The project includes synthetic CSV files so the app can be public, reproducible and safe to inspect. This avoids privacy risk while still showing the structure of an aggregate health analytics workflow.

### Prefer transparent scoring over black-box prediction

The scoring model uses min-max scaled indicators with visible weights. That makes the MVP easier to critique and reduces the risk of overstating model validity.

### Frame the map as planning signals, not disease reporting

The map includes a `Primary planning signal` mode. This shows the largest weighted component of the aggregate score. It does not rank diseases, report diagnoses or imply actual local prevalence beyond the synthetic demo data.

### Keep the report non-clinical

The selected-region Markdown report includes aggregate prescribing indicators, public-health indicators, a composite score and awareness/intervention categories. It avoids individual advice and medication-change recommendations.

## Architecture

The app follows a small but explicit analytics pipeline:

```text
Synthetic aggregate CSVs
        |
        v
Connector stubs and validation checks
        |
        v
pandas feature engineering
        |
        v
Transparent composite scoring
        |
        v
Streamlit dashboard and regional report export
```

Key modules:

| Area | File |
| --- | --- |
| Dashboard | `app/streamlit_app.py` |
| Feature engineering and scoring | `src/risk_model.py` |
| Connector boundary | `src/connectors.py` |
| Validation checks | `src/validation.py` |
| Tests | `tests/` |

## What The MVP Demonstrates

- Python project structure for a compact analytics product.
- pandas feature engineering over aggregate data.
- Streamlit and Plotly dashboard delivery.
- Interpretable risk-scoring logic.
- Public-health planning language rather than clinical decision-support language.
- Data governance, model-card and bias-review documentation.
- Test coverage for connector, validation, scoring and reporting functions.
- Deployment to Streamlit Community Cloud.

## Safety And Governance

The project treats health data framing as a product requirement, not an afterthought.

Built-in safeguards include:

- top-level dashboard disclaimer
- synthetic data notes
- explicit non-intended-use documentation
- model card
- data governance notes
- bias review template
- non-clinical report wording
- no secrets or API keys
- local open-data connector stubs with no live calls by default

## Trade-offs

| Decision | Benefit | Limitation |
| --- | --- | --- |
| Synthetic data | Safe public demo | Cannot support real regional conclusions |
| Weighted composite score | Easy to inspect and explain | Not clinically validated |
| Local CSV default | No secrets or external services required | No live data refresh |
| Streamlit app | Fast, accessible reviewer experience | Not production infrastructure |
| Connector stubs | Clear future integration boundary | Not full open-data ingestion yet |

## What I Would Improve Next

1. Add an optional local downloaded open-data mapping example.
2. Generate a data-quality report from validation results.
3. Add weight sensitivity analysis to show how ranking changes under alternative assumptions.
4. Add a small automated screenshot workflow for dashboard regression checks.
5. Expand documentation for real-world governance requirements before any real aggregate-data adaptation.

## Interview Narrative

The strongest part of this project is the boundary-setting. In healthtech, a dashboard is not enough; the product must also communicate what it is not. This MVP demonstrates how to combine domain-aware framing, simple analytics engineering, transparent scoring and responsible public documentation without drifting into unsafe clinical claims.
