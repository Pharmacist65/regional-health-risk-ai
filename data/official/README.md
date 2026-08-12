# Official aggregate data snapshot

This directory contains compact, analysis-ready tables derived from official
aggregate open-data releases. It contains no patient-level or identifiable
records. The raw workbooks and source exports are intentionally not committed;
the public repository keeps only the selected regional outputs needed by the
static explorer and tests.

Snapshot extract date: **2026-08-12**.

## Output inventory

| File | Geography | Coverage | Contents |
| --- | --- | --- | --- |
| `uk_regional_health_history.csv` | Nine English statistical regions | 2012/13-2024/25, indicator dependent | Seven QOF registered-prevalence series |
| `uk_health_index_history.csv` | Nine English statistical regions | 2015-2021 | ONS Health Index scores |
| `uk_regional_health_spending.csv` | Nine English statistical regions | 2020/21-2024/25 | Identifiable public expenditure on health per head |
| `us_state_health_history.csv` | 50 states and District of Columbia | 2019-2023, indicator dependent | Six age-adjusted adult prevalence series |
| `us_state_health_spending.csv` | 50 states and District of Columbia | 1991-2020 | All-payer personal health care expenditure per capita |
| `regional_forecasts.csv` | Same health geographies | Two periods after each series | Recent-window OLS outputs and diagnostics |

Coverage is source- and indicator-specific. The selected OHID statistical-region
series are complete for their current indicator IDs: most begin in 2012/13,
depression has 12 annual observations and asthma begins in 2020/21. The selected
refreshed CDC indicators begin in 2019; hypertension is available in 2019, 2021
and 2023. The CMS state-residence spending table is the full published 30-year
series.

## Source ledger

| Publisher | Dataset and selection | Source |
| --- | --- | --- |
| OHID / NHS England | Fingertips QOF indicators 219, 241, 253, 273, 276, 848 and 90933; statistical regions; persons; no category split | [Fingertips](https://fingertips.phe.org.uk/) |
| Office for National Statistics | Health Index scores, `Table_2_Index_scores`, region rows | [Health Index scores, England](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/healthandwellbeing/datasets/healthindexscoresengland) |
| HM Treasury | Country and Regional Analysis 2025, table A.15, function `7. Health` | [Country and Regional Analysis 2025](https://www.gov.uk/government/statistics/country-and-regional-analysis-2025) |
| Centers for Disease Control and Prevention | Chronic Disease Indicators AST02, CVD01, COPD01, DIA01, MEN02 and NPW14; overall; age-adjusted prevalence | [Chronic Disease Indicators](https://data.cdc.gov/d/hksd-2xuw) |
| Centers for Medicare & Medicaid Services | State Health Expenditure Accounts, residence table 11, personal health care per capita | [Health expenditures by state of residence](https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/state-residence) |

The source pages and their current reuse terms remain authoritative. UK source
materials are reused under the applicable Open Government Licence terms. US
federal source pages should be checked for dataset-specific notices before any
reuse beyond this portfolio demonstration.

## Transform rules

- UK disease values are registered prevalence from QOF. Denominators differ by
  indicator and are preserved in the output `population` field.
- US disease values are overall, age-adjusted adult prevalence estimates. The
  script excludes territories and retains the 50 states plus District of
  Columbia.
- UK spending is nominal GBP per head for identifiable public expenditure on
  health. US spending is nominal USD per capita for all-payer personal health
  care expenditure.
- Spending definitions and currencies differ. The dashboard never creates a
  UK-versus-US spending rank.
- UK QOF and US BRFSS/CDI prevalence measures differ in denominator, collection
  method and adjustment. The dashboard only ranks areas within the selected
  country and measure.
- Values are rounded only for compact public outputs. Available source 95%
  confidence limits are retained for health observations.
- Archived releases are not appended when definitions, denominators, regional
  boundaries or current-vintage revisions differ. Such extensions require a
  separately documented harmonisation study.

## Rebuild

Download the five official source files from the ledger, then run:

```bash
python scripts/build_regional_dataset.py \
  --uk-ohid path/to/fingertips_selected.csv \
  --uk-ons-index path/to/health_index_scores.xlsx \
  --uk-spending path/to/cra_2025_chapter_a.xlsx \
  --us-cdc path/to/cdi_selected.csv \
  --us-spending path/to/residence_all_tables.xlsx \
  --output-dir data/official \
  --dashboard-json docs/assets/regional_data.json \
  --extract-date YYYY-MM-DD
```

The builder makes no live API calls and requires no credentials. The exact
selection logic is version controlled in `scripts/build_regional_dataset.py`.

## Interpretation boundary

These files support descriptive population-health exploration and a transparent
short-horizon forecasting demonstration. They do not support diagnosis,
individual risk prediction, treatment decisions, causal claims or resource
allocation without further statistical, domain and governance review.
