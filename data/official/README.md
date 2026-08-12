# Official aggregate data snapshot

This directory contains compact, analysis-ready tables derived from official
aggregate open-data releases. It contains no patient-level or identifiable
records. The raw workbooks and source exports are intentionally not committed;
the public repository keeps only the selected regional outputs needed by the
static explorer and tests.

Snapshot extract date: **2026-08-13**.

## Output inventory

| File | Geography | Coverage | Contents |
| --- | --- | --- | --- |
| `uk_regional_health_history.csv` | Nine English statistical regions | 2012/13-2024/25, indicator dependent | Seven QOF registered-prevalence series |
| `uk_health_index_history.csv` | Nine English statistical regions | 2015-2021 | ONS Health Index scores |
| `uk_regional_health_spending.csv` | Nine English statistical regions | 2020/21-2024/25 | Identifiable public expenditure on health per head |
| `us_state_health_history.csv` | 50 states and District of Columbia | 2019-2023, indicator dependent | Six age-adjusted adult prevalence series |
| `us_state_health_spending.csv` | 50 states and District of Columbia | 1991-2020 | All-payer personal health care expenditure per capita |
| `regional_forecasts.csv` | Same health geographies | Two periods after each series | Recent-window OLS outputs and diagnostics |
| `regional_access_summary.csv` | Nine English regions and 50 states plus DC | Latest source-specific snapshots | Population, facility counts, per-100,000 density and operating/shortage context |
| `access_source_inventory.csv` | England and United States | Latest source-specific snapshots | Facility category definitions, record totals, periods and source URLs |

The static directory payloads in `docs/assets/facilities/` contain 60
area-specific JSON files. They are loaded only when an area is selected and
contain public organization or facility records, never patient records.

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
| Centers for Disease Control and Prevention | Chronic Disease Indicators AST02, CVD01, COPD01, DIA01, MEN02 and NPW14; overall; age-adjusted and crude prevalence | [Chronic Disease Indicators](https://data.cdc.gov/d/hksd-2xuw) |
| Centers for Medicare & Medicaid Services | State Health Expenditure Accounts, residence table 11, personal health care per capita | [Health expenditures by state of residence](https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/state-residence) |
| Office for National Statistics | Mid-2024 population estimates, `MYE2 - Persons`, English region rows | [UK population estimates](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland) |
| Care Quality Commission | 12 August 2026 care directory; hospital and Doctors/GP service-type locations | [Using CQC data](https://www.cqc.org.uk/about-us/transparency/using-cqc-data) |
| NHS Business Services Authority | Consolidated Pharmaceutical List, 2026/27 Q1; Community and LPS contracts | [Consolidated Pharmaceutical List](https://opendata.nhsbsa.net/dataset/consolidated-pharmaceutical-list) |
| U.S. Census Bureau | Vintage 2025 state population estimates; total and age 18+ | [State population by characteristics](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-state-detail.html) |
| Centers for Medicare & Medicaid Services | Hospital General Information, 28 April 2026 | [Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u) |
| Health Resources and Services Administration | Active Health Center Service Delivery and Look-Alike Sites, 12 August 2026 | [HRSA data downloads](https://data.hrsa.gov/data/download) |
| National Plan and Provider Enumeration System | Active organization NPIs with Community/Retail Pharmacy taxonomy and primary practice location, queried 13 August 2026 | [NPI Registry](https://npiregistry.cms.hhs.gov/) |
| Health Resources and Services Administration | Designated Primary Care Health Professional Shortage Areas, 12 August 2026 | [Shortage areas](https://data.hrsa.gov/topics/health-workforce/shortage-areas) |

The source pages and their current reuse terms remain authoritative. CQC and
NHSBSA directory data are available under the Open Government Licence v3.0;
the static site acknowledges both publishers. HRSA marks the selected health
center and HPSA files with no usage limitations. NPPES fields are
FOIA-disclosable public data. CMS notes that issuance of an NPI does not by
itself validate provider licensure or credentials.

## Transform rules

- UK disease values are registered prevalence from QOF. Indicator-specific
  register counts and registered-patient denominators are preserved.
- US chart values are overall, age-adjusted adult prevalence estimates. Crude
  prevalence and confidence limits are preserved separately for burden
  estimation. Territories are excluded.
- England burden is the official QOF register count. US burden is a planning
  estimate calculated from CDC crude prevalence and the same-year 2023 Census
  population aged 18+; its interval applies the CDC prevalence limits to that
  denominator.
- Facility density is the selected directory record count per 100,000 current
  residents. Categories retain their publisher definitions and are not merged
  into a composite adequacy score.
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

The regional health builder makes no live API calls and requires no credentials.
The exact selection logic is version controlled in
`scripts/build_regional_dataset.py`.

Create the compact NPPES organization extract from the official read API:

```bash
python scripts/download_nppes_pharmacies.py \
  --output path/to/nppes_community_pharmacies.csv \
  --snapshot-date YYYY-MM-DD
```

Then build the population and access layer from local official downloads:

```bash
python scripts/build_access_dataset.py \
  --uk-population path/to/ons_population.xlsx \
  --uk-cqc-directory path/to/cqc_directory.csv \
  --uk-pharmacies path/to/nhsbsa_pharmacies.csv \
  --us-population path/to/census_state_population.csv \
  --us-hospitals path/to/cms_hospitals.csv \
  --us-health-centers path/to/hrsa_health_centers.csv \
  --us-pharmacies path/to/nppes_community_pharmacies.csv \
  --us-hpsa path/to/hrsa_primary_care_hpsa.csv \
  --dashboard-json docs/assets/regional_data.json \
  --facility-output-dir docs/assets/facilities \
  --summary-csv data/official/regional_access_summary.csv \
  --source-inventory-csv data/official/access_source_inventory.csv \
  --extract-date YYYY-MM-DD
```

The access builder performs no network calls. The NPPES downloader uses only
the public API, queries primary practice locations, partitions capped states by
ZIP prefix and exports a restricted organization-level field set.

## Interpretation boundary

These files support descriptive population-health exploration and a transparent
short-horizon forecasting demonstration. They do not support diagnosis,
individual risk prediction, treatment decisions, causal claims or resource
allocation without further statistical, domain and governance review.
