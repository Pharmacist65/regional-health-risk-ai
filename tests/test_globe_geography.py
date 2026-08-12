import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEOGRAPHY_DATA = ROOT / "docs" / "assets" / "globe_geography.json"
DASHBOARD_DATA = ROOT / "docs" / "assets" / "regional_data.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rings(geometry: dict):
    if geometry["type"] == "Polygon":
        yield from geometry["coordinates"]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield from polygon
    else:
        raise AssertionError(f"Unsupported geometry type: {geometry['type']}")


def test_globe_geography_has_expected_display_coverage():
    geography = _load(GEOGRAPHY_DATA)

    assert geography["schema_version"] == "1.0"
    assert len(geography["countries"]["features"]) >= 170
    assert len(geography["regions"]["UK"]["features"]) == 9
    assert len(geography["regions"]["USA"]["features"]) == 51
    assert all(
        feature["properties"]["kind"] == "country"
        for feature in geography["countries"]["features"]
    )


def test_atlas_region_codes_match_dashboard_entities():
    geography = _load(GEOGRAPHY_DATA)
    dashboard = _load(DASHBOARD_DATA)

    for country in ("UK", "USA"):
        geography_codes = {
            feature["properties"]["area_code"]
            for feature in geography["regions"][country]["features"]
        }
        dashboard_codes = {
            entity["area_code"]
            for entity in dashboard["countries"][country]["entities"]
        }
        assert geography_codes == dashboard_codes


def test_display_geometries_are_closed_and_finite():
    geography = _load(GEOGRAPHY_DATA)
    feature_sets = [
        geography["countries"]["features"],
        geography["regions"]["UK"]["features"],
        geography["regions"]["USA"]["features"],
    ]

    for feature in (item for feature_set in feature_sets for item in feature_set):
        for ring in _rings(feature["geometry"]):
            assert len(ring) >= 4
            assert ring[0] == ring[-1]
            assert all(
                len(point) >= 2
                and math.isfinite(point[0])
                and math.isfinite(point[1])
                and -180 <= point[0] <= 180
                and -90 <= point[1] <= 90
                for point in ring
            )


def test_geography_bundle_retains_source_and_licence_metadata():
    geography = _load(GEOGRAPHY_DATA)
    sources = {source["id"]: source for source in geography["meta"]["sources"]}

    assert set(sources) == {
        "natural_earth_admin_0_110m",
        "us_census_tigerweb_states_2025",
        "ons_regions_december_2024_bfc",
    }
    assert sources["natural_earth_admin_0_110m"]["licence"] == "Public domain"
    assert "Open Government Licence" in sources["ons_regions_december_2024_bfc"]["licence"]
    assert "Contains OS data" in sources["ons_regions_december_2024_bfc"]["attribution"]
