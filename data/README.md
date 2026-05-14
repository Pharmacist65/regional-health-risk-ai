# Data notes

## Default data

The CSV files in this folder are synthetic aggregate demo data. They are not NHS data and must not be interpreted as evidence about the named regions.

- `sample_aggregate_prescribing.csv`: monthly area-level medication-class indicators
- `sample_public_health_indicators.csv`: synthetic area-level public-health indicators

The application uses these files by default so it can run locally without API keys, secrets, patient records or external downloads.

## Prescribing schema

`sample_aggregate_prescribing.csv` uses this aggregate schema:

| Column | Meaning |
| --- | --- |
| `month` | Month for the aggregate observation, formatted as `YYYY-MM-DD` |
| `area_code` | Public area identifier |
| `area_name` | Area display name |
| `medication_class` | One of `NSAID`, `Antihypertensive`, `Lipid-lowering`, `Antidiabetic` |
| `items_per_1000` | Synthetic item rate per 1,000 population |
| `cost_per_1000` | Synthetic cost rate per 1,000 population |

## Public-health schema

`sample_public_health_indicators.csv` uses this aggregate schema:

| Column | Meaning |
| --- | --- |
| `area_code` | Public area identifier |
| `area_name` | Area display name |
| `latitude` | Approximate map latitude |
| `longitude` | Approximate map longitude |
| `saturated_fat_proxy_index` | Synthetic contextual indicator, 0 to 100 |
| `deprivation_index` | Synthetic contextual indicator, 0 to 100 |
| `obesity_prevalence_pct` | Synthetic aggregate percentage |
| `hypertension_prevalence_estimate_pct` | Synthetic aggregate percentage |
| `diabetes_prevalence_estimate_pct` | Synthetic aggregate percentage |

## Using local aggregate open data

Future real-data experiments should use local downloaded aggregate CSVs with the same schemas. Put any local working files under `data/local/`; that folder is ignored by git to avoid accidentally committing large extracts or data with unclear provenance.

The connector stubs in `src/connectors.py` accept local CSV paths. They do not make live API calls or require API keys.

## Safety boundary

Do not add patient-level records, simulated identifiable patients, private credentials or source files that imply NHS affiliation. Any real open-data adaptation should document provenance, licences, transformations, aggregation level and validation results.
