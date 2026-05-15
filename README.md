# Regional Preventive Health Analytics

[![Tests](https://github.com/Pharmacist65/regional-health-risk-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/Pharmacist65/regional-health-risk-ai/actions/workflows/tests.yml)

A privacy-first portfolio proof-of-concept for population-level preventive health analytics using synthetic aggregate prescribing and public health indicators.

> Not affiliated with the NHS. Not medical advice. This repository does not process patient-level data.

## Product snapshot

The dashboard is built as an interactive Streamlit app rather than a static notebook. It includes a regional overview, a score explanation layer and a downloadable non-clinical planning report for the selected area.

![Dashboard overview](docs/images/dashboard_overview.jpg)

![Regional report generator](docs/images/regional_report.jpg)

## What this project demonstrates

This project turns a public-health concept into a working software MVP:

- aggregate medication usage analytics
- transparent regional prevention-prioritisation scoring
- dashboard-based area comparison and selected-area review
- pharmacy and primary-care awareness workflow prompts
- privacy-first design with no patient records

The goal is to demonstrate healthtech/data engineering capability, not to provide clinical decision support.

## Problem framing

Preventable disease progression can be influenced by medication-use patterns, adherence issues, medication-lifestyle risk factors and local public health indicators. Many signals are visible at population level and can support prevention planning when handled responsibly.

## Data position

The included CSV files are **synthetic demo data**. They are included so recruiters and reviewers can run the dashboard locally without API keys, secrets or access to patient records.

`src/connectors.py` includes placeholder interfaces for future OpenPrescribing-style aggregate prescribing data and OHID/Fingertips-style public health indicators. These stubs read local synthetic CSVs by default and do not make live API calls.

A real version of this project could be adapted to aggregate/open sources such as:

- NHSBSA English Prescribing Data: https://www.nhsbsa.nhs.uk/prescription-data/prescribing-data/english-prescribing-data-epd
- OpenPrescribing: https://openprescribing.net/
- OHID Fingertips public health profiles: https://fingertips.phe.org.uk/

## Using local aggregate open data

The default runtime path remains the synthetic CSV files in `data/`. For future experiments, the connector stubs can load local downloaded aggregate CSVs that match the documented schemas in [data/README.md](data/README.md).

The project intentionally does not make live API calls, require API keys or process patient-level records.

## Architecture

```text
Aggregate prescribing data      Public health indicators
            |                              |
            v                              v
      Data preparation --------------> Area features
                                            |
                                            v
                                  Composite risk scoring
                                            |
                                            v
                     Dashboard + prevention-prioritisation review
```

## Repository structure

```text
app/
  streamlit_app.py              # interactive dashboard
src/
  connectors.py                # open-data connector stubs with synthetic fallback
  data_pipeline.py              # synthetic data generator
  validation.py                 # aggregate input validation checks
  risk_model.py                 # feature builder and risk score
data/
  README.md
  sample_aggregate_prescribing.csv
  sample_public_health_indicators.csv
docs/
  architecture.md
  data_governance.md
  deployment.md
  ethics_privacy.md
  images/
  model_card.md
  project_brief.md
  portfolio_pitch.md
  scoring_methodology.md
tests/
  test_connectors.py
  test_risk_model.py
  test_validation.py
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```

The app opens a Streamlit dashboard with a regional score ranking, map, selected-area trend, score component breakdown and downloadable regional Markdown report.

## Documentation

- [Model card](docs/model_card.md) - intended use, non-intended use, assumptions, limitations and ethical boundaries
- [Architecture](docs/architecture.md) - system flow and component overview
- [Data governance](docs/data_governance.md) - validation checks, data boundaries and real-data readiness
- [Deployment](docs/deployment.md) - Streamlit Community Cloud deployment checklist
- [Ethics and privacy](docs/ethics_privacy.md) - governance and privacy framing
- [Portfolio pitch](docs/portfolio_pitch.md) - recruiter-facing summary and interview talking points
- [Scoring methodology](docs/scoring_methodology.md) - scoring assumptions, weights and limitations

## Method summary

The demonstration score combines min-max scaled values for:

- persistent NSAID exposure signal
- cardiometabolic prescribing density
- saturated-fat proxy index
- deprivation index
- obesity prevalence estimate

These weights are illustrative and are not clinically validated.

## Ethical boundaries

This project is a public-health analytics proof of concept, not a clinical tool.

It does not:

- use individual patient data
- diagnose disease
- recommend treatment changes
- replace GP, pharmacist or public-health judgement

It does:

- use aggregate area-level indicators
- produce interpretable risk signals
- suggest non-clinical awareness and workflow actions
- prioritise privacy and governance by design

## Roadmap

- [ ] Replace synthetic data with documented aggregate open data connectors
- [x] Add OpenPrescribing/OHID connector stubs with synthetic fallback
- [x] Add aggregate data validation and governance documentation
- [ ] Add live OpenPrescribing API integration examples
- [ ] Add live OHID Fingertips indicator mapping
- [x] Add model-card documentation
- [ ] Add bias review template
- [ ] Add Streamlit Cloud deployment
- [x] Add selected-region Markdown report export
