# Model card

## Model name

Regional preventive health analytics demo score.

## Summary

This repository demonstrates an interpretable, population-level prevention-prioritisation score using synthetic aggregate prescribing indicators and synthetic public-health indicators. It is a portfolio proof of concept, not a deployed clinical model.

## Intended use

- Explore how aggregate medication-class trends and public-health context can be combined for regional prevention planning.
- Demonstrate privacy-first health analytics, feature engineering, transparent scoring and Streamlit dashboard delivery.
- Support portfolio conversations with recruiters, hiring managers and healthtech stakeholders.
- Provide a safe local example that can run without API keys, secrets or patient-level data.

## Non-intended use

This project must not be used for:

- diagnosis, triage or individual risk prediction
- treatment advice, prescribing advice, dosing advice or supplement advice
- patient-level clinical decision support
- replacing pharmacist, GP, public-health or clinical-safety judgement
- claiming NHS approval, NHS endorsement or NHS affiliation

## Data assumptions

- Included data is synthetic and aggregate by area.
- Prescribing rows represent medication-class item rates per 1,000 population, not individual prescriptions.
- Public-health indicators are synthetic area-level proxies.
- Area names and codes are used to make the demo realistic, but the values are not evidence about those places.
- A real implementation would require documented data provenance, aggregation thresholds, refresh logic, quality checks and governance approval.

## Model assumptions

The demo score uses min-max scaled area-level features:

- NSAID persistence signal: 35%
- Cardiometabolic prescribing density: 25%
- Saturated-fat proxy index: 20%
- Deprivation index: 10%
- Obesity prevalence estimate: 10%

The score is intentionally transparent and rule-based. The weights are illustrative and not clinically validated.

## Outputs

The application produces:

- ranked area-level demo risk scores
- score tiers for dashboard filtering
- an interpretable component breakdown
- non-clinical prevention workflow prompts
- a downloadable selected-region Markdown report with aggregate prescribing indicators, public-health indicators and non-clinical awareness categories

Outputs are designed for planning conversations only. They do not identify patients or advise actions for individuals.

## Limitations

- Synthetic data cannot support real conclusions about any region.
- Min-max scaling is sensitive to the demo dataset range.
- Weights are not validated against outcomes.
- The score does not account for confounding, uncertainty, demographic structure or service capacity.
- Suggested actions are generic workflow prompts, not evidence of local need.
- The demo does not include production data ingestion, monitoring, authentication, audit logging or deployment controls.

## Ethical boundaries

- Preserve privacy by default: no patient-level records, no identifiable simulated patients and no private credentials.
- Keep the framing as aggregate public-health analytics, not clinical AI.
- Avoid treatment, prescribing, dosing, supplement or individual medical advice.
- Make assumptions visible so reviewers can challenge the method.
- Require governance, validation, bias review and clinical-safety review before any real-world adaptation.

## Disclaimer

This software is not affiliated with the NHS. It is not medical advice. It uses no patient-level data. It is a portfolio demonstration of aggregate public-health analytics.
