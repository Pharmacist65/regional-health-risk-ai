import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import download_nppes_pharmacies
from src.access_data import transform_us_pharmacies


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "official" / "regional_access_summary.csv"
INVENTORY_PATH = ROOT / "data" / "official" / "access_source_inventory.csv"
DASHBOARD_PATH = ROOT / "docs" / "assets" / "regional_data.json"
FACILITY_DIR = ROOT / "docs" / "assets" / "facilities"
CATEGORIES = ("hospital", "primary_care", "pharmacy")


def _dashboard() -> dict:
    return json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))


def _facility_payload(country: str, area_code: str) -> dict:
    path = FACILITY_DIR / country.lower() / f"{area_code.lower()}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_access_summary_has_complete_population_and_unique_area_coverage():
    summary = pd.read_csv(SUMMARY_PATH)

    assert len(summary) == 60
    assert summary.groupby("country").size().to_dict() == {"UK": 9, "USA": 51}
    assert not summary.duplicated(["country", "area_code"]).any()
    assert (summary["population"] > 0).all()
    assert set(summary.loc[summary["country"].eq("UK"), "population_year"]) == {2024}
    assert set(summary.loc[summary["country"].eq("USA"), "population_year"]) == {2025}

    for category in CATEGORIES:
        assert (summary[f"{category}_count"] > 0).all()
        expected = summary[f"{category}_count"] / summary["population"] * 100_000
        assert summary[f"{category}_per_100k"].tolist() == pytest.approx(
            expected.round(2).tolist()
        )


def test_facility_payloads_match_summary_counts_and_use_unique_ids():
    summary = pd.read_csv(SUMMARY_PATH)
    files = list(FACILITY_DIR.glob("*/*.json"))
    assert len(files) == 60

    for row in summary.itertuples(index=False):
        payload = _facility_payload(row.country, row.area_code)
        assert payload["country"] == row.country
        assert payload["area_code"] == row.area_code
        assert payload["area_name"] == row.area_name
        for category in CATEGORIES:
            category_payload = payload["categories"][category]
            records = category_payload["records"]
            ids = [record["id"] for record in records]
            assert len(records) == getattr(row, f"{category}_count")
            assert len(ids) == len(set(ids))
            assert all(record.get("name") for record in records)
            assert category_payload["source_url"].startswith("https://")


def test_dashboard_access_values_match_compact_summary():
    summary = pd.read_csv(SUMMARY_PATH).set_index(["country", "area_code"])
    payload = _dashboard()

    for country_code, country in payload["countries"].items():
        for entity in country["entities"]:
            row = summary.loc[(country_code, entity["area_code"])]
            access = entity["access"]
            assert access["population"]["value"] == row["population"]
            assert access["population"]["year"] == row["population_year"]
            assert access["facility_file"].endswith(
                f"/{entity['area_code'].lower()}.json"
            )
            assert {item["key"] for item in access["capacity"]} == set(CATEGORIES)
            for item in access["capacity"]:
                category = item["key"]
                assert item["count"] == row[f"{category}_count"]
                assert item["per_100k"] == row[f"{category}_per_100k"]
                assert item["source_url"].startswith("https://")


def test_england_burden_uses_qof_register_count_and_denominator():
    payload = _dashboard()

    for entity in payload["countries"]["UK"]["entities"]:
        for metric in entity["metrics"].values():
            burden = metric["burden"]
            assert burden["kind"] == "recorded"
            assert 0 < burden["value"] <= burden["denominator"]
            calculated_rate = burden["value"] / burden["denominator"] * 100
            assert calculated_rate == pytest.approx(burden["prevalence"], abs=0.02)
            assert burden["value"] == round(metric["latest_numerator"])
            assert burden["denominator"] == round(metric["latest_denominator"])


def test_us_burden_uses_crude_prevalence_and_same_year_adult_population():
    payload = _dashboard()

    for entity in payload["countries"]["USA"]["entities"]:
        for metric in entity["metrics"].values():
            burden = metric["burden"]
            assert burden["kind"] == "modelled"
            assert burden["population_year"] == 2023
            assert burden["lower"] <= burden["value"] <= burden["upper"]
            assert burden["value"] == round(
                burden["denominator"] * burden["prevalence"] / 100
            )
            assert burden["prevalence"] == metric["latest_crude_value"]


def test_access_source_inventory_is_auditable_and_matches_record_totals():
    inventory = pd.read_csv(INVENTORY_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    payload = _dashboard()

    assert len(inventory) == 6
    assert not inventory.duplicated(["country", "category"]).any()
    assert inventory["source_url"].str.startswith("https://").all()
    for row in inventory.itertuples(index=False):
        expected = summary.loc[
            summary["country"].eq(row.country), f"{row.category}_count"
        ].sum()
        assert row.record_count == expected

    source_ids = {source["id"] for source in payload["sources"]}
    assert {
        "uk_population",
        "uk_facilities",
        "uk_pharmacies",
        "us_population",
        "us_hospitals",
        "us_primary_care",
        "us_pharmacies",
        "us_shortage",
    }.issubset(source_ids)
    assert "determination of adequacy" in payload["meta"]["access_boundary"]


def test_public_facility_payloads_exclude_authorized_official_fields():
    forbidden = "authorized_official"

    for path in FACILITY_DIR.glob("*/*.json"):
        text = path.read_text(encoding="utf-8").lower()
        assert forbidden not in text


def test_nppes_queries_are_restricted_to_primary_practice_locations(monkeypatch):
    captured = []

    def fake_request(parameters):
        captured.append(parameters)
        return {"results": []}

    monkeypatch.setattr(download_nppes_pharmacies, "_request_json", fake_request)
    records, capped = download_nppes_pharmacies._fetch_partition(
        "CA",
        "2026-08-13",
        postal_prefix="90",
        page_size=200,
    )

    assert records == []
    assert capped is False
    assert captured[0]["address_purpose"] == "PRIMARY"
    assert captured[0]["state"] == "CA"
    assert captured[0]["postal_code"] == "90*"


def test_nppes_records_without_a_published_name_get_a_traceable_label(tmp_path):
    source_path = tmp_path / "pharmacies.csv"
    pd.DataFrame(
        [
            {
                "npi": "1598696601",
                "name": None,
                "address": "253 COMMERCIAL BLVD STE B",
                "city": "LAUDERDALE BY THE SEA",
                "state": "FL",
                "postal_code": "333084528",
                "phone": "954-683-5950",
            }
        ]
    ).to_csv(source_path, index=False)

    transformed = transform_us_pharmacies(source_path)

    assert transformed.loc[0, "name"] == "NPI organization 1598696601"
    assert transformed.loc[0, "postal_code"] == "33308-4528"
