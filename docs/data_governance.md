# Data governance

## Purpose

This public repository demonstrates aggregate public-health analytics through a
synthetic Streamlit MVP and an official regional research explorer.

## Data boundary

Allowed:

- synthetic aggregate prescribing and public-health indicators
- official aggregate regional health and spending tables
- public geography identifiers, centroids and generalised display boundaries
- source confidence limits, definitions and provenance

Not allowed:

- patient-level or row-level clinical records
- identifiable or simulated identifiable people
- private prescribing extracts
- API keys, tokens, credentials or local handoff notes
- diagnosis, treatment or individual-risk outputs

`LOCAL_SESSION_HANDOFF.md`, `.venv/`, caches and local working extracts are
ignored and must remain outside commits. Raw downloaded source workbooks are
kept outside the repository; only compact selected aggregate outputs are public.

## Official source governance

Every official output carries geography, period, measure type, population,
publisher and source URL. The snapshot extract date is 2026-08-12. Source
publication periods remain visible and are not relabelled as current-year data.

The source ledger, selections and rebuild command are documented in
`data/official/README.md`. Source pages and their current reuse terms are
authoritative.

The map bundle is governed separately from the health snapshot. It contains
only generalised public boundary coordinates and names. Natural Earth country
geometry is public domain; US state geometry is sourced from the US Census
Bureau; ONS digital boundaries are reused under the Open Government Licence
v3.0 with the required ONS and Ordnance Survey attribution shown in the static
site footer and source ledger.

## Comparability controls

- England QOF registered prevalence is not ranked against US BRFSS/CDI
  age-adjusted adult prevalence.
- Indicator-specific denominators are displayed with the selected measure.
- UK and US spending retain separate definitions and currencies.
- England coverage is described as nine statistical regions, not full UK data.
- Scotland, Wales and Northern Ireland require separate definition-preserving
  views before inclusion.

## Validation checks

The synthetic path validates required columns, dates, missing area identifiers,
duplicate aggregate keys, unknown medication classes, negative rates and
public-health indicator ranges.

The official snapshot tests validate:

- expected geography and metric coverage
- unique area/metric/year keys
- prevalence and confidence-interval ordering
- positive spending values and documented periods
- two-period forecast horizons and 0-100 bounds
- source URLs and dashboard interpretation metadata
- display-geography coverage, ring validity and licence metadata

These are engineering and data-integrity checks, not clinical validation.

## Forecast governance

Forecasts are deterministic recent-window OLS baselines. Training periods,
observation counts, fit statistics and rolling errors are preserved. Forecasts
are omitted when fewer than four observations are available. The displayed
interval is explicitly described as exploratory residual variation.

No output may be used to automate service, funding or clinical decisions without
independent validation and governance.

## Contribution hypotheses

Possible contributor cards are evidence-linked prompts for further analysis.
They are not generated causal findings. Regional co-occurrence cannot establish
individual or area-level causation, and prompts should not be used to stigmatise
communities.

## Change control

Before refreshing or extending official data:

1. Record publisher, dataset version, extract date and licence terms.
2. Review measure and geography definition changes.
3. Update explicit indicator selections in the builder.
4. Rebuild compact outputs from local source files.
5. Run all unit and data-integrity tests.
6. Review the dashboard for missingness and changed interpretation.
7. Update the source ledger and model card before publication.

## Operational gap

The repository has no production authentication, access logging, monitoring,
data-retention service or clinical-safety case. It is suitable for public
portfolio review, not operational healthcare use.
