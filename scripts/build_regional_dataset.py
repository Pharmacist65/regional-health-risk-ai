"""Build compact official aggregate datasets for the static regional explorer.

This script reads locally downloaded source files. It never calls a live API,
requires no credentials, and does not process patient-level data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.regional_forecasting import forecast_recent_trend
from src.regional_hypotheses import serialise_hypothesis_registry


UK_INDICATORS = {
    219: {
        "key": "hypertension",
        "label": "Hypertension registered prevalence",
        "population": "All registered patients",
    },
    241: {
        "key": "diabetes",
        "label": "Diabetes registered prevalence",
        "population": "Registered patients aged 17+",
    },
    253: {
        "key": "copd",
        "label": "COPD registered prevalence",
        "population": "All registered patients",
    },
    273: {
        "key": "chd",
        "label": "Coronary heart disease registered prevalence",
        "population": "All registered patients",
    },
    276: {
        "key": "cancer",
        "label": "Cancer registered prevalence",
        "population": "All registered patients",
    },
    848: {
        "key": "depression",
        "label": "Depression registered prevalence",
        "population": "Registered patients aged 18+",
    },
    90933: {
        "key": "asthma",
        "label": "Asthma registered prevalence",
        "population": "Registered patients aged 6+",
    },
}

US_INDICATORS = {
    "AST02": {"key": "asthma", "label": "Current asthma among adults"},
    "CVD01": {"key": "hypertension", "label": "High blood pressure among adults"},
    "COPD01": {"key": "copd", "label": "COPD among adults"},
    "DIA01": {"key": "diabetes", "label": "Diabetes among adults"},
    "MEN02": {"key": "depression", "label": "Depression among adults"},
    "NPW14": {"key": "obesity", "label": "Obesity among adults"},
}

UK_REGIONS = {
    "E12000001": ("North East", 54.9783, -1.6178),
    "E12000002": ("North West", 53.7632, -2.7031),
    "E12000003": ("Yorkshire and the Humber", 53.9915, -1.5412),
    "E12000004": ("East Midlands", 52.98, -0.75),
    "E12000005": ("West Midlands", 52.4751, -1.8298),
    "E12000006": ("East of England", 52.2405, 0.4179),
    "E12000007": ("London", 51.5074, -0.1278),
    "E12000008": ("South East", 51.2787, -0.5217),
    "E12000009": ("South West", 50.7772, -3.9995),
}

US_REGION_STATES = {
    "New England": "CT ME MA NH RI VT".split(),
    "Mideast": "DE DC MD NJ NY PA".split(),
    "Great Lakes": "IL IN MI OH WI".split(),
    "Plains": "IA KS MN MO NE ND SD".split(),
    "Southeast": "AL AR FL GA KY LA MS NC SC TN VA WV".split(),
    "Southwest": "AZ NM OK TX".split(),
    "Rocky Mountain": "CO ID MT UT WY".split(),
    "Far West": "AK CA HI NV OR WA".split(),
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

STATE_TO_REGION = {
    state: region
    for region, states in US_REGION_STATES.items()
    for state in states
}
STATE_NAME_TO_CODE = {name: code for code, name in STATE_NAMES.items()}

SOURCE_URLS = {
    "uk_ohid": "https://fingertips.phe.org.uk/",
    "uk_ons_index": (
        "https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/"
        "healthandwellbeing/datasets/healthindexscoresengland"
    ),
    "uk_spending": "https://www.gov.uk/government/statistics/country-and-regional-analysis-2025",
    "us_cdc": "https://data.cdc.gov/d/hksd-2xuw",
    "us_spending": (
        "https://www.cms.gov/data-research/statistics-trends-and-reports/"
        "national-health-expenditure-data/state-residence"
    ),
}


def _normalise_uk_region_name(name: object) -> str:
    value = str(name).replace(" region (statistical)", "").strip()
    replacements = {
        "Yorkshire and The Humber": "Yorkshire and the Humber",
        "East": "East of England",
    }
    return replacements.get(value, value)


def transform_uk_health(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, low_memory=False)
    selected = source[
        source["Indicator ID"].isin(UK_INDICATORS)
        & source["Area Code"].isin(UK_REGIONS)
        & source["Area Type"].eq("Regions (statistical)")
        & source["Sex"].eq("Persons")
        & source["Category Type"].isna()
    ].copy()
    selected["value"] = pd.to_numeric(selected["Value"], errors="coerce")
    selected = selected.dropna(subset=["value"])
    selected["metric_key"] = selected["Indicator ID"].map(
        lambda value: UK_INDICATORS[int(value)]["key"]
    )
    selected["metric_label"] = selected["Indicator ID"].map(
        lambda value: UK_INDICATORS[int(value)]["label"]
    )
    selected["population"] = selected["Indicator ID"].map(
        lambda value: UK_INDICATORS[int(value)]["population"]
    )
    selected["area_name"] = selected["Area Name"].map(_normalise_uk_region_name)
    selected["year"] = selected["Time period"].str.extract(r"^(\d{4})")[0].astype(int)
    output = pd.DataFrame(
        {
            "country": "UK",
            "area_code": selected["Area Code"],
            "area_name": selected["area_name"],
            "macro_region": "England",
            "metric_key": selected["metric_key"],
            "metric_label": selected["metric_label"],
            "year": selected["year"],
            "period": selected["Time period"],
            "value": selected["value"].round(3),
            "lower_ci": pd.to_numeric(selected["Lower CI 95.0 limit"], errors="coerce").round(3),
            "upper_ci": pd.to_numeric(selected["Upper CI 95.0 limit"], errors="coerce").round(3),
            "unit": "% registered prevalence",
            "population": selected["population"],
            "measure_type": "QOF registered prevalence",
            "source_id": selected["Indicator ID"].astype(str),
            "source_name": "OHID Fingertips / NHS England QOF",
            "source_url": SOURCE_URLS["uk_ohid"],
        }
    )
    return output.sort_values(["area_code", "metric_key", "year"]).reset_index(drop=True)


def transform_uk_health_index(source_path: Path) -> pd.DataFrame:
    source = pd.read_excel(source_path, sheet_name="Table_2_Index_scores", header=2)
    source = source[source["Area Type [Note 3]"].eq("Region")].copy()
    year_columns = [
        column for column in source.columns if re.fullmatch(r"20\d{2}", str(column))
    ]
    melted = source.melt(
        id_vars=["Area Code", "Area Name"],
        value_vars=year_columns,
        var_name="year",
        value_name="health_index",
    )
    melted["year"] = melted["year"].astype(int)
    melted["area_name"] = melted["Area Name"].map(_normalise_uk_region_name)
    return pd.DataFrame(
        {
            "country": "UK",
            "area_code": melted["Area Code"],
            "area_name": melted["area_name"],
            "year": melted["year"],
            "health_index": pd.to_numeric(melted["health_index"], errors="coerce").round(2),
            "unit": "Index (England 2015 = 100; higher is better)",
            "source_name": "Office for National Statistics Health Index",
            "source_url": SOURCE_URLS["uk_ons_index"],
        }
    ).sort_values(["area_code", "year"])


def transform_uk_spending(source_path: Path) -> pd.DataFrame:
    source = pd.read_excel(source_path, sheet_name="A.15", header=None)
    health_column = next(
        index
        for index in source.columns
        if source[index].astype(str).str.strip().eq("7. Health").any()
    )
    region_to_code = {name: code for code, (name, _, _) in UK_REGIONS.items()}
    rows: list[dict[str, object]] = []
    active_period: str | None = None
    for _, row in source.iterrows():
        label = str(row.iloc[0]).strip()
        if re.fullmatch(r"\d{4}-\d{2}", label):
            active_period = label
            continue
        area_name = _normalise_uk_region_name(label)
        if active_period is None or area_name not in region_to_code:
            continue
        value = pd.to_numeric(row.iloc[health_column], errors="coerce")
        if pd.isna(value):
            continue
        rows.append(
            {
                "country": "UK",
                "area_code": region_to_code[area_name],
                "area_name": area_name,
                "macro_region": "England",
                "year": int(active_period[:4]),
                "period": active_period,
                "spending_per_capita": round(float(value), 2),
                "currency": "GBP",
                "measure_type": "Identifiable public expenditure on health per head",
                "source_name": "HM Treasury Country and Regional Analysis 2025",
                "source_url": SOURCE_URLS["uk_spending"],
            }
        )
    return pd.DataFrame(rows).sort_values(["area_code", "year"]).reset_index(drop=True)


def _parse_point(value: object) -> tuple[float | None, float | None]:
    match = re.search(r"POINT \(([-\d.]+) ([-\d.]+)\)", str(value))
    if not match:
        return None, None
    return float(match.group(2)), float(match.group(1))


def transform_us_health(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, low_memory=False)
    selection = source["locationabbr"].isin(STATE_NAMES) & source["questionid"].isin(
        US_INDICATORS
    )
    if "stratificationcategory1" in source:
        selection &= source["stratificationcategory1"].eq("Overall")
    if "stratification1" in source:
        selection &= source["stratification1"].eq("Overall")
    if "datavaluetype" in source:
        selection &= source["datavaluetype"].eq("Age-adjusted Prevalence")
    selected = source[selection].copy()
    selected["value"] = pd.to_numeric(selected["datavalue"], errors="coerce")
    selected = selected.dropna(subset=["value"])
    selected["metric_key"] = selected["questionid"].map(
        lambda value: US_INDICATORS[str(value)]["key"]
    )
    selected["metric_label"] = selected["questionid"].map(
        lambda value: US_INDICATORS[str(value)]["label"]
    )
    points = selected["geolocation"].map(_parse_point)
    selected["latitude"] = points.map(lambda value: value[0])
    selected["longitude"] = points.map(lambda value: value[1])
    return pd.DataFrame(
        {
            "country": "USA",
            "area_code": selected["locationabbr"],
            "area_name": selected["locationdesc"],
            "macro_region": selected["locationabbr"].map(STATE_TO_REGION),
            "latitude": selected["latitude"],
            "longitude": selected["longitude"],
            "metric_key": selected["metric_key"],
            "metric_label": selected["metric_label"],
            "year": selected["yearstart"].astype(int),
            "period": selected["yearstart"].astype(int).astype(str),
            "value": selected["value"].round(3),
            "lower_ci": pd.to_numeric(selected["lowconfidencelimit"], errors="coerce").round(3),
            "upper_ci": pd.to_numeric(selected["highconfidencelimit"], errors="coerce").round(3),
            "unit": "% age-adjusted prevalence",
            "population": "Adults aged 18+",
            "measure_type": "BRFSS age-adjusted prevalence",
            "source_id": selected["questionid"],
            "source_name": "CDC Chronic Disease Indicators",
            "source_url": SOURCE_URLS["us_cdc"],
        }
    ).sort_values(["area_code", "metric_key", "year"]).reset_index(drop=True)


def transform_us_spending(source_path: Path) -> pd.DataFrame:
    source = pd.read_excel(
        source_path,
        sheet_name="Table 11 Personal Health Care",
        header=1,
    )
    area_column = source.columns[0]
    source["area_code"] = source[area_column].map(STATE_NAME_TO_CODE)
    source = source[source["area_code"].notna()].copy()
    year_columns = [column for column in source.columns if isinstance(column, (int, float))]
    melted = source.melt(
        id_vars=[area_column, "area_code"],
        value_vars=year_columns,
        var_name="year",
        value_name="spending_per_capita",
    )
    melted["year"] = melted["year"].astype(int)
    return pd.DataFrame(
        {
            "country": "USA",
            "area_code": melted["area_code"],
            "area_name": melted[area_column],
            "macro_region": melted["area_code"].map(STATE_TO_REGION),
            "year": melted["year"],
            "period": melted["year"].astype(str),
            "spending_per_capita": pd.to_numeric(
                melted["spending_per_capita"], errors="coerce"
            ).round(2),
            "currency": "USD",
            "measure_type": "All-payer personal health care expenditure per capita",
            "source_name": "CMS State Health Expenditure Accounts",
            "source_url": SOURCE_URLS["us_spending"],
        }
    ).sort_values(["area_code", "year"]).reset_index(drop=True)


def _forecast_records(health: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (country, area_code, metric_key), series in health.groupby(
        ["country", "area_code", "metric_key"]
    ):
        last_year = int(series["year"].max())
        try:
            forecast = forecast_recent_trend(
                series["year"],
                series["value"],
                future_years=[last_year + 1, last_year + 2],
                bounds=(0, 100),
            )
        except ValueError:
            continue
        for point in forecast.points:
            rows.append(
                {
                    "country": country,
                    "area_code": area_code,
                    "metric_key": metric_key,
                    "year": point.year,
                    "forecast_value": point.value,
                    "lower": point.lower,
                    "upper": point.upper,
                    "model_name": forecast.model_name,
                    "observations": forecast.observations,
                    "training_start_year": forecast.training_start_year,
                    "training_end_year": forecast.training_end_year,
                    "slope_per_year": forecast.slope_per_year,
                    "r_squared": forecast.r_squared,
                    "backtest_mae": forecast.backtest_mae,
                    "backtest_smape_pct": forecast.backtest_smape_pct,
                    "quality": forecast.quality,
                }
            )
    return pd.DataFrame(rows).sort_values(["country", "area_code", "metric_key", "year"])


def _records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    clean = frame[columns].copy()
    clean = clean.where(pd.notna(clean), None)
    return clean.to_dict("records")


def _build_dashboard_payload(
    uk_health: pd.DataFrame,
    us_health: pd.DataFrame,
    uk_spending: pd.DataFrame,
    us_spending: pd.DataFrame,
    uk_index: pd.DataFrame,
    forecasts: pd.DataFrame,
    *,
    extract_date: str,
) -> dict[str, object]:
    all_health = pd.concat([uk_health, us_health], ignore_index=True)
    all_spending = pd.concat([uk_spending, us_spending], ignore_index=True)
    countries: dict[str, object] = {}

    for country in ("UK", "USA"):
        country_health = all_health[all_health["country"].eq(country)]
        country_spending = all_spending[all_spending["country"].eq(country)]
        country_forecasts = forecasts[forecasts["country"].eq(country)]
        entities: list[dict[str, object]] = []
        for area_code, area_health in country_health.groupby("area_code"):
            profile = area_health.iloc[0]
            spending = country_spending[country_spending["area_code"].eq(area_code)]
            entity_metrics: dict[str, object] = {}
            for metric_key, metric_history in area_health.groupby("metric_key"):
                metric_history = metric_history.sort_values("year")
                latest = metric_history.iloc[-1]
                metric_forecasts = country_forecasts[
                    country_forecasts["area_code"].eq(area_code)
                    & country_forecasts["metric_key"].eq(metric_key)
                ]
                model = None
                if not metric_forecasts.empty:
                    model_row = metric_forecasts.iloc[0]
                    model = {
                        "name": model_row["model_name"],
                        "observations": int(model_row["observations"]),
                        "training_start_year": int(model_row["training_start_year"]),
                        "training_end_year": int(model_row["training_end_year"]),
                        "slope_per_year": model_row["slope_per_year"],
                        "r_squared": model_row["r_squared"],
                        "backtest_mae": model_row["backtest_mae"],
                        "backtest_smape_pct": model_row["backtest_smape_pct"],
                        "quality": model_row["quality"],
                        "points": _records(
                            metric_forecasts,
                            ["year", "forecast_value", "lower", "upper"],
                        ),
                    }
                entity_metrics[metric_key] = {
                    "label": latest["metric_label"],
                    "unit": latest["unit"],
                    "population": latest["population"],
                    "measure_type": latest["measure_type"],
                    "source_id": str(latest["source_id"]),
                    "source_name": latest["source_name"],
                    "source_url": latest["source_url"],
                    "latest_value": latest["value"],
                    "latest_period": latest["period"],
                    "history": _records(
                        metric_history,
                        ["year", "period", "value", "lower_ci", "upper_ci"],
                    ),
                    "forecast": model,
                }

            latitude = None
            longitude = None
            if country == "UK":
                _, latitude, longitude = UK_REGIONS[str(area_code)]
            else:
                latitude = profile.get("latitude")
                longitude = profile.get("longitude")
            index_history = uk_index[uk_index["area_code"].eq(area_code)]
            entities.append(
                {
                    "area_code": area_code,
                    "area_name": profile["area_name"],
                    "macro_region": profile["macro_region"],
                    "latitude": latitude,
                    "longitude": longitude,
                    "metrics": entity_metrics,
                    "spending": {
                        "currency": None if spending.empty else spending.iloc[-1]["currency"],
                        "measure_type": None if spending.empty else spending.iloc[-1]["measure_type"],
                        "source_name": None if spending.empty else spending.iloc[-1]["source_name"],
                        "source_url": None if spending.empty else spending.iloc[-1]["source_url"],
                        "latest_value": None if spending.empty else spending.iloc[-1]["spending_per_capita"],
                        "latest_period": None if spending.empty else spending.iloc[-1]["period"],
                        "history": _records(
                            spending,
                            ["year", "period", "spending_per_capita"],
                        ),
                    },
                    "health_index": _records(
                        index_history,
                        ["year", "health_index"],
                    ),
                }
            )

        countries[country] = {
            "label": "United Kingdom" if country == "UK" else "United States",
            "coverage_note": (
                "Nine English statistical regions; devolved nations use separate definitions."
                if country == "UK"
                else "50 states and District of Columbia, grouped into eight CMS regions."
            ),
            "default_metric": "diabetes",
            "metrics": {
                metric_key: {
                    "label": metric_rows.iloc[0]["metric_label"],
                    "unit": metric_rows.iloc[0]["unit"],
                    "measure_type": metric_rows.iloc[0]["measure_type"],
                }
                for metric_key, metric_rows in country_health.groupby("metric_key")
            },
            "entities": sorted(entities, key=lambda item: str(item["area_name"])),
        }

    return {
        "meta": {
            "title": "Regional Preventive Health Analytics",
            "extract_date": extract_date,
            "data_boundary": "Official aggregate open data only; no patient-level records.",
            "interpretation_boundary": (
                "Descriptive and exploratory planning analysis. Forecasts are not clinical predictions; "
                "hypotheses are not causal findings."
            ),
            "cross_country_warning": (
                "UK QOF registered prevalence and US BRFSS age-adjusted prevalence use different "
                "populations and methods and must not be directly ranked against each other."
            ),
        },
        "countries": countries,
        "hypotheses": serialise_hypothesis_registry(),
        "sources": [
            {
                "id": source_id,
                "url": url,
            }
            for source_id, url in SOURCE_URLS.items()
        ],
    }


def write_outputs(
    *,
    uk_health: pd.DataFrame,
    uk_index: pd.DataFrame,
    uk_spending: pd.DataFrame,
    us_health: pd.DataFrame,
    us_spending: pd.DataFrame,
    output_dir: Path,
    dashboard_json: Path,
    extract_date: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_json.parent.mkdir(parents=True, exist_ok=True)
    forecasts = _forecast_records(pd.concat([uk_health, us_health], ignore_index=True))
    datasets = {
        "uk_regional_health_history.csv": uk_health,
        "uk_health_index_history.csv": uk_index,
        "uk_regional_health_spending.csv": uk_spending,
        "us_state_health_history.csv": us_health,
        "us_state_health_spending.csv": us_spending,
        "regional_forecasts.csv": forecasts,
    }
    for filename, frame in datasets.items():
        frame.to_csv(output_dir / filename, index=False)

    payload = _build_dashboard_payload(
        uk_health,
        us_health,
        uk_spending,
        us_spending,
        uk_index,
        forecasts,
        extract_date=extract_date,
    )
    dashboard_json.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uk-ohid", type=Path, required=True)
    parser.add_argument("--uk-ons-index", type=Path, required=True)
    parser.add_argument("--uk-spending", type=Path, required=True)
    parser.add_argument("--us-cdc", type=Path, required=True)
    parser.add_argument("--us-spending", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/official"))
    parser.add_argument(
        "--dashboard-json",
        type=Path,
        default=Path("docs/assets/regional_data.json"),
    )
    parser.add_argument("--extract-date", default="2026-08-12")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_outputs(
        uk_health=transform_uk_health(args.uk_ohid),
        uk_index=transform_uk_health_index(args.uk_ons_index),
        uk_spending=transform_uk_spending(args.uk_spending),
        us_health=transform_us_health(args.us_cdc),
        us_spending=transform_us_spending(args.us_spending),
        output_dir=args.output_dir,
        dashboard_json=args.dashboard_json,
        extract_date=args.extract_date,
    )


if __name__ == "__main__":
    main()
