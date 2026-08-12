# Deployment

## Static regional explorer

`docs/index.html` and `docs/assets/` form a no-build static site. For local review:

```bash
python -m http.server 8765 --directory docs
```

Open `http://127.0.0.1:8765/`.

The directory is published through GitHub Pages from branch `main`, folder
`/docs`:

[https://pharmacist65.github.io/regional-health-risk-ai/](https://pharmacist65.github.io/regional-health-risk-ai/)

No build step, server runtime or secret is required. The repository README links
directly to this stable project URL. A 1280x720 walkthrough video is served from
`docs/media/regional-health-atlas-demo.mp4`.

Publication checks:

- run the full test suite and JSON/JavaScript syntax checks
- review desktop and mobile rendering
- verify England/US controls, geographic hover/click, source links and WebGL fallback
- verify burden calculations, capacity median markers and all facility tabs
- verify area-specific facility JSON loads, search and record links on GitHub Pages
- confirm the pinned Globe.GL CDN asset loads and the local dotted fallback is usable
- confirm all committed records are aggregate and publicly reusable
- retain the cross-country comparability and non-clinical warnings

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
