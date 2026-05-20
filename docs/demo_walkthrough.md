# Demo Walkthrough

## Purpose

This walkthrough is for recruiters, hiring managers and technical reviewers who want to understand the project quickly without reading every source file first.

The live app is a portfolio demonstration of aggregate public-health analytics. It uses synthetic area-level data only and does not provide clinical advice.

Live demo: [Regional Preventive Health Analytics](https://regional-health-risk-ai-ikqhu3ynfpabw2emgxg6br.streamlit.app/)

## Two-minute review path

1. Open the live dashboard.
2. Read the disclaimer panel at the top of the page.
3. Review the four headline metrics: areas analysed, highest demo score, medication classes and aggregate rows.
4. In `Regional overview`, compare the ranked prevention-prioritisation score chart with the geographic map.
5. Use the sidebar `Map colour` control to switch from `Risk tier` to `Primary planning signal`.
6. Open the `Selected area` tab and inspect:
   - selected-area score and tier
   - primary planning signal
   - medication-class trend
   - score component breakdown
   - public-health indicator snapshot
7. Download or preview the regional Markdown report.
8. Open `Method and governance` to check the scoring weights and safety assumptions.

## What To Notice

- The app is interactive, not a static notebook.
- The method is transparent: score components and weights are visible.
- The map shows aggregate planning signals, not disease rankings.
- The report generator is explicitly non-clinical.
- The project includes tests, documentation and governance notes rather than only dashboard code.
- Synthetic data is the default runtime path, so the demo can be public without patient-data risk.

## Technical Review Path

Useful files for a code review:

| Area | File |
| --- | --- |
| Streamlit dashboard | `app/streamlit_app.py` |
| Feature engineering and scoring | `src/risk_model.py` |
| Connector boundary | `src/connectors.py` |
| Input validation | `src/validation.py` |
| Synthetic data notes | `data/README.md` |
| Tests | `tests/` |
| Architecture | `docs/architecture.md` |
| Model assumptions | `docs/model_card.md` |
| Scoring method | `docs/scoring_methodology.md` |
| Governance checks | `docs/data_governance.md` and `docs/bias_review_template.md` |

## What Not To Infer

Do not interpret this demo as:

- real evidence about any named area
- a clinical model
- an individual risk predictor
- a diagnosis or triage tool
- prescribing, dosing, treatment or supplement advice
- an NHS-affiliated product

## Interview Talking Points

- Why synthetic aggregate data is used by default.
- How the project separates public-health planning support from clinical decision support.
- Why the score is interpretable rather than black-box.
- How connector stubs allow future aggregate open-data integration without making live API calls by default.
- What validation and governance would be needed before any real-data adaptation.
- How Streamlit, pandas, Plotly and pytest are used together in a compact healthtech MVP.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```
