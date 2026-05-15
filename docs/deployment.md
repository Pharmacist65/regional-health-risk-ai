# Deployment

## Streamlit Community Cloud checklist

This app is designed to deploy without secrets because it uses synthetic local CSV data by default.

Current public deployment:

[https://regional-health-risk-ai-ikqhu3ynfpabw2emgxg6br.streamlit.app/](https://regional-health-risk-ai-ikqhu3ynfpabw2emgxg6br.streamlit.app/)

Recommended deployment settings:

| Setting | Value |
| --- | --- |
| Repository | `Pharmacist65/regional-health-risk-ai` |
| Branch | `main` |
| Main file path | `app/streamlit_app.py` |
| Python dependencies | `requirements.txt` |
| Secrets | None required |

## Pre-deployment checks

Run locally before deploying:

```bash
pytest
streamlit run app/streamlit_app.py
```

Confirm:

- the dashboard loads from the synthetic CSV files
- no API keys or secrets are required
- the disclaimer panel is visible
- the selected-region report download works
- no patient-level data is present

## README deployment link

The repository README includes the live demo link near the top of the page so reviewers can open the dashboard without cloning the project.

## Safety boundary

The deployed app must remain a portfolio demonstration using synthetic aggregate data unless a separate governance process approves a documented aggregate open-data adaptation.
