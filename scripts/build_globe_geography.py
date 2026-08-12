"""Build the compact geography bundle used by the static 3D atlas.

The output contains public country boundaries plus the analytical region shapes
used by the England and United States views. Source geometries are simplified
for browser rendering; they are not intended for legal or survey use.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "globe_geography.json"

NATURAL_EARTH_GEOJSON = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)
NATURAL_EARTH_PAGE = (
    "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/"
    "110m-admin-0-countries/"
)
CENSUS_SERVICE = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/State_County/MapServer/16/query"
)
ONS_SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Regions_December_2024_Boundaries_EN_BFC/FeatureServer/0/query"
)

US_AREA_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}
ENGLAND_REGION_CODES = {f"E1200000{index}" for index in range(1, 10)}


def _service_url(base: str, params: dict[str, str]) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"


CENSUS_GEOJSON = _service_url(
    CENSUS_SERVICE,
    {
        "where": "STATE IS NOT NULL",
        "outFields": "STATE,STUSAB,BASENAME,NAME,CENTLAT,CENTLON",
        "returnGeometry": "true",
        "outSR": "4326",
        "geometryPrecision": "4",
        "maxAllowableOffset": "0.02",
        "f": "geojson",
    },
)
ONS_GEOJSON = _service_url(
    ONS_SERVICE,
    {
        "where": "RGN24CD IS NOT NULL",
        "outFields": "RGN24CD,RGN24NM,LONG,LAT",
        "returnGeometry": "true",
        "outSR": "4326",
        "geometryPrecision": "4",
        "maxAllowableOffset": "0.01",
        "f": "geojson",
    },
)


def _read_json(source: str) -> dict[str, Any]:
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    request = urllib.request.Request(source, headers={"User-Agent": "regional-health-risk-ai/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def _point_distance(point: list[float], start: list[float], end: list[float]) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    position = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)
    position = max(0.0, min(1.0, position))
    nearest_x = start[0] + position * dx
    nearest_y = start[1] + position * dy
    return math.hypot(point[0] - nearest_x, point[1] - nearest_y)


def _rdp(points: list[list[float]], tolerance: float) -> list[list[float]]:
    if len(points) <= 2:
        return points
    maximum = 0.0
    split_index = 0
    for index in range(1, len(points) - 1):
        distance = _point_distance(points[index], points[0], points[-1])
        if distance > maximum:
            maximum = distance
            split_index = index
    if maximum <= tolerance:
        return [points[0], points[-1]]
    left = _rdp(points[: split_index + 1], tolerance)
    right = _rdp(points[split_index:], tolerance)
    return left[:-1] + right


def _signed_area(ring: list[list[float]]) -> float:
    return sum(
        start[0] * end[1] - end[0] * start[1]
        for start, end in zip(ring, ring[1:])
    ) / 2


def _simplify_ring(
    ring: Iterable[Iterable[float]], tolerance: float
) -> list[list[float]] | None:
    points = [[round(float(point[0]), 4), round(float(point[1]), 4)] for point in ring]
    if len(points) < 4:
        return None
    if points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 3:
        return None

    # Starting at the point furthest from the first avoids simplifying a closed
    # ring against a zero-length segment.
    anchor = max(range(1, len(points)), key=lambda index: _point_distance(points[index], points[0], points[0]))
    ordered = points[anchor:] + points[:anchor] + [points[anchor]]
    simplified = _rdp(ordered, tolerance)
    if len(simplified) < 4:
        return None
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified


def _simplify_polygon(
    polygon: list[list[list[float]]], tolerance: float, minimum_area: float
) -> list[list[list[float]]] | None:
    rings: list[list[list[float]]] = []
    for index, ring in enumerate(polygon):
        simplified = _simplify_ring(ring, tolerance)
        if simplified is None:
            continue
        if index > 0 and abs(_signed_area(simplified)) < minimum_area:
            continue
        rings.append(simplified)
    return rings or None


def _simplify_geometry(
    geometry: dict[str, Any], tolerance: float, minimum_area: float
) -> dict[str, Any]:
    geometry_type = geometry["type"]
    coordinates = geometry["coordinates"]
    if geometry_type == "Polygon":
        polygon = _simplify_polygon(coordinates, tolerance, minimum_area)
        if polygon is None:
            raise ValueError("Polygon was removed during simplification")
        return {"type": geometry_type, "coordinates": polygon}
    if geometry_type == "MultiPolygon":
        polygons = [
            simplified
            for polygon in coordinates
            if (simplified := _simplify_polygon(polygon, tolerance, minimum_area)) is not None
        ]
        if not polygons:
            raise ValueError("MultiPolygon was removed during simplification")
        return {"type": geometry_type, "coordinates": polygons}
    raise ValueError(f"Unsupported geometry type: {geometry_type}")


def _country_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    features = []
    for feature in payload["features"]:
        properties = feature["properties"]
        code = properties.get("ADM0_A3") or properties.get("ISO_A3")
        name = properties.get("NAME_EN") or properties.get("NAME")
        if code == "ATA":
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": "country",
                    "area_code": code,
                    "area_name": name,
                },
                "geometry": _simplify_geometry(feature["geometry"], 0.04, 0.0001),
            }
        )
    return features


def _regional_features(
    payload: dict[str, Any], country: str
) -> list[dict[str, Any]]:
    features = []
    if country == "USA":
        code_key, name_key = "STUSAB", "BASENAME"
        allowed_codes = US_AREA_CODES
        tolerance, minimum_area = 0.008, 0.00002
    else:
        code_key, name_key = "RGN24CD", "RGN24NM"
        allowed_codes = ENGLAND_REGION_CODES
        tolerance, minimum_area = 0.004, 0.000002

    for feature in payload["features"]:
        properties = feature["properties"]
        code = properties.get(code_key)
        if code not in allowed_codes:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": "region",
                    "country": country,
                    "area_code": code,
                    "area_name": properties[name_key],
                },
                "geometry": _simplify_geometry(feature["geometry"], tolerance, minimum_area),
            }
        )
    features.sort(key=lambda feature: feature["properties"]["area_code"])
    if {feature["properties"]["area_code"] for feature in features} != allowed_codes:
        raise ValueError(f"Unexpected {country} regional coverage")
    return features


def build_bundle(world_source: str, us_source: str, england_source: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "meta": {
            "purpose": "Generalised display geography for the static regional atlas",
            "geography_warning": "Display geometry only; not for legal or survey use.",
            "sources": [
                {
                    "id": "natural_earth_admin_0_110m",
                    "publisher": "Natural Earth",
                    "vintage": "1:110m Admin 0 countries",
                    "url": NATURAL_EARTH_PAGE,
                    "licence": "Public domain",
                },
                {
                    "id": "us_census_tigerweb_states_2025",
                    "publisher": "U.S. Census Bureau",
                    "vintage": "January 1, 2025 states",
                    "url": CENSUS_SERVICE.rsplit("/16/query", 1)[0],
                    "licence": "United States government work; source attribution requested",
                },
                {
                    "id": "ons_regions_december_2024_bfc",
                    "publisher": "Office for National Statistics",
                    "vintage": "December 2024 England regions, BFC",
                    "url": ONS_SERVICE.rsplit("/0/query", 1)[0],
                    "licence": "Open Government Licence v3.0; contains OS data",
                    "attribution": (
                        "Source: Office for National Statistics licensed under the Open "
                        "Government Licence v.3.0. Contains OS data \u00a9 Crown copyright "
                        "and database right 2024."
                    ),
                },
            ],
        },
        "countries": {
            "type": "FeatureCollection",
            "features": _country_features(_read_json(world_source)),
        },
        "regions": {
            "UK": {
                "type": "FeatureCollection",
                "features": _regional_features(_read_json(england_source), "UK"),
            },
            "USA": {
                "type": "FeatureCollection",
                "features": _regional_features(_read_json(us_source), "USA"),
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-source", default=NATURAL_EARTH_GEOJSON)
    parser.add_argument("--us-source", default=CENSUS_GEOJSON)
    parser.add_argument("--england-source", default=ONS_GEOJSON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    bundle = build_bundle(args.world_source, args.us_source, args.england_source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {args.output} with {len(bundle['countries']['features'])} countries, "
        f"{len(bundle['regions']['USA']['features'])} US areas and "
        f"{len(bundle['regions']['UK']['features'])} England regions."
    )


if __name__ == "__main__":
    main()
