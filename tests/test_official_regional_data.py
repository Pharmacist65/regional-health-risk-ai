import json
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "official"
DASHBOARD_DATA = ROOT / "docs" / "assets" / "regional_data.json"

UK_METRICS = {
    "asthma",
    "cancer",
    "chd",
    "copd",
    "depression",
    "diabetes",
    "hypertension",
}
US_METRICS = {
    "asthma",
    "copd",
    "depression",
    "diabetes",
    "hypertension",
    "obesity",
}


def _read(filename: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / filename)


def test_health_history_has_expected_country_coverage_and_unique_keys():
    uk = _read("uk_regional_health_history.csv")
    us = _read("us_state_health_history.csv")

    assert uk["area_code"].nunique() == 9
    assert set(uk["metric_key"]) == UK_METRICS
    assert len(uk[["area_code", "metric_key"]].drop_duplicates()) == 9 * len(UK_METRICS)
    assert not uk.duplicated(["area_code", "metric_key", "year"]).any()

    assert us["area_code"].nunique() == 51
    assert us["macro_region"].nunique() == 8
    assert set(us["metric_key"]) == US_METRICS
    assert len(us[["area_code", "metric_key"]].drop_duplicates()) == 51 * len(US_METRICS)
    assert not us.duplicated(["area_code", "metric_key", "year"]).any()


def test_health_values_and_confidence_intervals_are_well_formed():
    for filename in ("uk_regional_health_history.csv", "us_state_health_history.csv"):
        frame = _read(filename)
        assert frame["value"].notna().all()
        assert frame["value"].between(0, 100).all()
        assert (frame["lower_ci"] <= frame["value"]).all()
        assert (frame["value"] <= frame["upper_ci"]).all()
        assert frame["source_url"].str.startswith("https://").all()


def test_health_history_preserves_count_and_crude_prevalence_inputs():
    uk = _read("uk_regional_health_history.csv")
    us = _read("us_state_health_history.csv")

    assert uk[["numerator", "denominator"]].notna().all().all()
    assert (uk["numerator"] > 0).all()
    assert (uk["numerator"] <= uk["denominator"]).all()
    assert (uk["numerator"] / uk["denominator"] * 100).tolist() == pytest.approx(
        uk["value"].tolist(), abs=0.02
    )

    crude = us.dropna(subset=["crude_value", "crude_lower_ci", "crude_upper_ci"])
    assert len(crude) >= len(us) - 1
    assert (crude["crude_lower_ci"] <= crude["crude_value"]).all()
    assert (crude["crude_value"] <= crude["crude_upper_ci"]).all()
    latest = us.sort_values("year").groupby(["area_code", "metric_key"]).tail(1)
    assert latest[["crude_value", "crude_lower_ci", "crude_upper_ci"]].notna().all().all()


def test_health_history_matches_documented_comparable_periods():
    uk = _read("uk_regional_health_history.csv")
    us = _read("us_state_health_history.csv")

    uk_periods = uk.groupby("metric_key")["year"].agg(["min", "max", "nunique"])
    assert tuple(uk_periods.loc["asthma"]) == (2020, 2024, 5)
    assert tuple(uk_periods.loc["depression"]) == (2012, 2024, 12)
    for metric in UK_METRICS - {"asthma", "depression"}:
        assert tuple(uk_periods.loc[metric]) == (2012, 2024, 13)

    us_periods = us.groupby("metric_key")["year"].agg(["min", "max", "nunique"])
    assert tuple(us_periods.loc["hypertension"]) == (2019, 2023, 3)
    for metric in US_METRICS - {"hypertension"}:
        assert tuple(us_periods.loc[metric]) == (2019, 2023, 5)


def test_spending_history_matches_documented_periods():
    uk = _read("uk_regional_health_spending.csv")
    us = _read("us_state_health_spending.csv")

    assert set(uk.groupby("area_code").size()) == {5}
    assert (uk["year"].min(), uk["year"].max()) == (2020, 2024)
    assert set(us.groupby("area_code").size()) == {30}
    assert (us["year"].min(), us["year"].max()) == (1991, 2020)
    assert not uk.duplicated(["area_code", "year"]).any()
    assert not us.duplicated(["area_code", "year"]).any()
    assert (uk["spending_per_capita"] > 0).all()
    assert (us["spending_per_capita"] > 0).all()


def test_forecasts_are_short_horizon_bounded_and_auditable():
    forecasts = _read("regional_forecasts.csv")

    assert not forecasts.duplicated(
        ["country", "area_code", "metric_key", "year"]
    ).any()
    assert (forecasts["year"] > forecasts["training_end_year"]).all()
    assert (forecasts["year"] <= forecasts["training_end_year"] + 2).all()
    assert forecasts["forecast_value"].between(0, 100).all()
    assert (forecasts["lower"] <= forecasts["forecast_value"]).all()
    assert (forecasts["forecast_value"] <= forecasts["upper"]).all()
    assert forecasts["model_name"].eq("Recent-window ordinary least squares").all()


def test_dashboard_payload_preserves_boundaries_and_coverage():
    payload = json.loads(DASHBOARD_DATA.read_text(encoding="utf-8"))

    assert payload["meta"]["extract_date"] == "2026-08-13"
    assert "no patient-level" in payload["meta"]["data_boundary"].lower()
    assert "person-level records" in payload["meta"]["data_boundary"].lower()
    assert "must not be directly ranked" in payload["meta"]["cross_country_warning"]
    assert len(payload["countries"]["UK"]["entities"]) == 9
    assert len(payload["countries"]["USA"]["entities"]) == 51
    assert set(payload["countries"]["UK"]["metrics"]) == UK_METRICS
    assert set(payload["countries"]["USA"]["metrics"]) == US_METRICS
    assert all(source["url"].startswith("https://") for source in payload["sources"])
