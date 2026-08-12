# Architecture

## System overview

The repository now has two deliberately separate analytical surfaces. The
official-data explorer supports descriptive regional research; the original
Streamlit MVP demonstrates a synthetic prevention-planning workflow. They share
the same aggregate-only safety boundary but do not silently mix their data.

```text
OFFICIAL REGIONAL RESEARCH

Local official downloads
OHID | ONS | HMT | CDC | CMS
            |
            v
scripts/build_regional_dataset.py
  selection + normalisation + provenance
            |
            +----> data/official/*.csv
            |
            +----> src/regional_forecasting.py
            |        recent-window OLS + backtest diagnostics
            |
            +----> src/regional_hypotheses.py
            |        evidence-linked research prompts
            |
            v
docs/assets/regional_data.json
            |
            v
docs/index.html + dashboard.js + dashboard.css
  static UK/USA explorer + dotted WebGL/canvas atlas

Natural Earth | US Census TIGERweb | ONS Open Geography
            |
            v
scripts/build_globe_geography.py
  simplification + display-only provenance
            |
            v
docs/assets/globe_geography.json


SYNTHETIC PRODUCT MVP

Synthetic aggregate CSVs
            |
            v
connectors -> validation -> quality report -> feature engineering
            |
            v
transparent composite score
            |
            v
Streamlit dashboard + regional Markdown report
```

## Official data build

`scripts/build_regional_dataset.py` reads five local source files and does not
call live APIs. It selects documented indicators and geographies, normalises
fields, preserves measure definitions and source URLs, and writes compact CSV
tables plus the static dashboard JSON.

The build includes:

- nine English statistical regions with OHID QOF prevalence
- ONS regional Health Index history
- HM Treasury regional health expenditure per head
- 50 US states plus District of Columbia with CDC CDI age-adjusted prevalence
- CMS state personal health care expenditure per capita

Raw downloads remain outside version control. Selected aggregate outputs are
committed with provenance and integrity tests.

`scripts/build_globe_geography.py` is a separate display-geography build. It
normalises and simplifies Natural Earth country boundaries, 2025 US Census
state boundaries and December 2024 ONS England-region boundaries into a compact
browser bundle. These geometries support navigation only and are not analytical,
legal or survey boundaries.

## Forecast layer

`src/regional_forecasting.py` is a pure, deterministic module. It cleans annual
series, fits recent-window OLS, performs rolling-origin backtesting and returns a
two-period projection with diagnostics and an exploratory residual band. It has
no clinical labels, hidden features or patient inputs.

## Hypothesis layer

`src/regional_hypotheses.py` stores reviewed prompts and evidence links by metric.
The selected area's position against a same-country median determines only the
context sentence. It does not infer which candidate domain caused the value.

## Static dashboard

`docs/index.html` is a no-build static application suitable for local review and
future GitHub Pages hosting. `docs/assets/dashboard.js` loads the versioned JSON,
manages country/area/indicator controls, renders SVG history and spending charts,
and creates a Globe.GL/Three.js dotted globe. Geographic hover is resolved from
the pointer coordinate against the bundled GeoJSON, so highlighting does not add
overlapping polygon meshes. If WebGL or the pinned external script is unavailable,
a local dotted-canvas fallback keeps the view functional.

UK and US selectors have separate metric dictionaries. Cross-country rankings
are not implemented by design.

## Synthetic Streamlit path

The existing `app/streamlit_app.py` path keeps its synthetic fallback and
transparent composite scoring. `src/connectors.py`, `src/open_data_mapping.py`,
`src/validation.py`, `src/quality_report.py` and `src/risk_model.py` remain its
primary modules.

## Verification

Tests cover transform-independent forecasting behavior, interval bounds,
non-causal hypothesis language, official output geography/metric coverage,
duplicate keys, confidence-interval ordering, spending periods, forecast
horizons and dashboard metadata.
The display-geography tests also enforce country/region counts, exact agreement
with dashboard area codes, finite closed rings and retained licence metadata.

## Safety boundary

No component may ingest patient-level records, infer individual disease risk,
provide diagnosis or treatment advice, automate resource allocation or claim
government/NHS endorsement. Any operational adaptation would require separate
statistical validation, privacy review, clinical-safety review and governance.
