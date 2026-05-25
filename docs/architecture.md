# Architecture

## System overview

This project is intentionally small: local CSV files flow through connector stubs, validation checks, a pandas feature layer, a transparent scoring layer and a Streamlit dashboard. The default data is synthetic aggregate data, so the app can be reviewed publicly without patient privacy risk.

```text
Synthetic aggregate CSVs      Future aggregate open-data sources
          |                         OpenPrescribing / OHID
          |                                  |
          |                                  v
          |                    src.open_data_mapping offline CSV mapping
          |                                  |
          v                                  v
      data files <-------------- src.connectors stubs
          |
          v
  src.validation schema and quality checks
          |
          +----> src.quality_report dashboard summary
          |
          v
  src.risk_model feature builder
          |
          v
 transparent composite scoring + tiers
          |
          v
 Streamlit dashboard, charts and regional Markdown report export
```

## Components

### Data layer

The demo reads two CSV files from `data/`:

- `sample_aggregate_prescribing.csv`: monthly area-level medication-class item and cost rates
- `sample_public_health_indicators.csv`: synthetic area-level public-health context

`src/data_pipeline.py` can regenerate the synthetic sample data. A production adaptation would replace this layer with validated aggregate open-data connectors and keep synthetic data as a fallback.

`src/connectors.py` defines the future connector boundary:

- `load_openprescribing_aggregate_prescribing()` for OpenPrescribing-style aggregate prescribing data
- `load_ohid_fingertips_public_health_indicators()` for OHID/Fingertips-style public-health indicators

Both functions currently return local synthetic CSV data by default. They do not make live API calls, require API keys or process patient-level records.

`src/open_data_mapping.py` provides an optional offline mapping layer for downloaded aggregate open-data CSVs:

- `map_openprescribing_aggregate_csv()` maps OpenPrescribing-style aggregate prescribing extracts into the internal prescribing schema.
- `map_ohid_fingertips_indicator_csv()` maps OHID/Fingertips-style long indicator extracts into the internal public-health schema.

This layer is deliberately separate from the default dashboard runtime. It supports local experimentation while keeping the public demo synthetic and reproducible.

### Validation layer

`src/validation.py` checks aggregate input quality before data reaches the scoring pipeline. It validates required columns, parseable dates, missing area identifiers, duplicate rows, unknown medication classes, negative values and public-health indicator ranges.

These checks are not clinical validation. They are data-quality guardrails for a portfolio analytics workflow.

`src/quality_report.py` turns those validation outcomes into a compact quality report for the dashboard and documentation. It summarises row counts, area counts, missingness, blank values, duplicate aggregate keys and issue counts for each input dataset.

### Feature layer

`src/risk_model.py` validates required columns and converts monthly medication-class rows into one row per area. Derived features include:

- NSAID mean items per 1,000 population
- months above the area NSAID median
- cardiometabolic prescribing density
- public-health context indicators joined by area

### Scoring layer

The composite score uses min-max scaled features with visible weights. This keeps the method explainable for portfolio review and avoids implying a validated clinical prediction model.

The scoring layer also generates non-clinical prevention workflow prompts. These prompts are for aggregate planning discussions only.

The scoring layer exposes the largest weighted score component as a primary planning signal. This is used for map exploration and selected-area explanation. It is not a disease ranking or evidence of reported local diagnoses.

### Dashboard layer

`app/streamlit_app.py` provides:

- a top-level disclaimer panel
- regional score ranking
- map view by risk tier or primary aggregate planning signal
- selected-area medication-class trend
- score component breakdown
- public-health indicator snapshot for the selected area
- data-quality snapshot for aggregate input datasets
- ranked intervention table
- downloadable regional Markdown report with aggregate prescribing and public-health indicators

## Testing

Tests live in `tests/` and focus on pure connector, validation, data-processing and scoring functions. The GitHub Actions workflow installs the documented requirements and runs `pytest`.

## Current stack

- Python
- pandas
- Streamlit
- Plotly
- pytest

## Future integration points

- OpenPrescribing aggregate prescribing connector
- OHID Fingertips public-health indicator connector
- local downloaded CSV mapping for OpenPrescribing/OHID-style aggregate extracts
- documented data-quality checks
- dashboard data-quality report export
- data governance documentation
- exportable regional reports in CSV or PDF
- Streamlit Cloud deployment

## Safety boundary

The architecture must remain aggregate and public-health oriented. It must not ingest patient-level records, provide diagnosis, recommend treatment, provide dosing advice or claim NHS affiliation.
