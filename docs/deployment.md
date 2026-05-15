# Deployment

## Streamlit Community Cloud checklist

This app is designed to deploy without secrets because it uses synthetic local CSV data by default.

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

## README update after deployment

After the app is deployed, add a short `Live demo` section near the top of `README.md`:

```markdown
## Live demo

[Open the dashboard](https://your-streamlit-app-url)
```

Only add this after the deployment URL is working.

## Safety boundary

The deployed app must remain a portfolio demonstration using synthetic aggregate data unless a separate governance process approves a documented aggregate open-data adaptation.
