"""Population, facility and access transforms for the regional explorer.

All functions operate on locally downloaded aggregate or public directory files.
No patient-level or person-level health records are processed.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import pandas as pd


UK_REGION_CODES = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and the Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
}
UK_REGION_NAME_TO_CODE = {name: code for code, name in UK_REGION_CODES.items()}

US_STATE_NAMES = {
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
US_STATE_FIPS_TO_CODE = {
    1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT",
    10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI", 16: "ID",
    17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
    23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS",
    29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ",
    35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK",
    41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN",
    48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV",
    55: "WI", 56: "WY",
}

ACCESS_SOURCES: dict[str, dict[str, str]] = {
    "uk_population": {
        "name": "Office for National Statistics mid-year population estimates",
        "url": (
            "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/"
            "populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland"
        ),
        "period": "Mid-2024",
    },
    "uk_facilities": {
        "name": "Care Quality Commission care directory",
        "url": "https://www.cqc.org.uk/about-us/transparency/using-cqc-data",
        "period": "12 August 2026",
    },
    "uk_pharmacies": {
        "name": "NHSBSA Consolidated Pharmaceutical List",
        "url": "https://opendata.nhsbsa.net/dataset/consolidated-pharmaceutical-list",
        "period": "2026/27 Q1",
    },
    "us_population": {
        "name": "U.S. Census Bureau Vintage 2025 population estimates",
        "url": "https://www.census.gov/data/datasets/time-series/demo/popest/2020s-state-detail.html",
        "period": "1 July 2025",
    },
    "us_hospitals": {
        "name": "CMS Hospital General Information",
        "url": "https://data.cms.gov/provider-data/dataset/xubh-q36u",
        "period": "28 April 2026",
    },
    "us_primary_care": {
        "name": "HRSA Health Center Service Delivery and Look-Alike Sites",
        "url": "https://data.hrsa.gov/data/download",
        "period": "12 August 2026",
    },
    "us_pharmacies": {
        "name": "CMS National Plan and Provider Enumeration System",
        "url": "https://npiregistry.cms.hhs.gov/api-page",
        "period": "13 August 2026 query snapshot",
    },
    "us_shortage": {
        "name": "HRSA Primary Care Health Professional Shortage Areas",
        "url": "https://data.hrsa.gov/topics/health-workforce/shortage-areas",
        "period": "12 August 2026",
    },
}

FACILITY_DEFINITIONS: dict[str, dict[str, dict[str, str]]] = {
    "UK": {
        "hospital": {
            "label": "Hospital locations",
            "definition": "CQC-regulated locations with a hospital service type.",
            "source_id": "uk_facilities",
        },
        "primary_care": {
            "label": "Doctor / GP locations",
            "definition": "CQC-regulated locations with a Doctors/GPs service type.",
            "source_id": "uk_facilities",
        },
        "pharmacy": {
            "label": "NHS pharmacy sites",
            "definition": "Community and Local Pharmaceutical Services entries in the NHS pharmaceutical list.",
            "source_id": "uk_pharmacies",
        },
    },
    "USA": {
        "hospital": {
            "label": "Medicare-registered hospitals",
            "definition": "Hospitals registered with Medicare in CMS Hospital General Information.",
            "source_id": "us_hospitals",
        },
        "primary_care": {
            "label": "HRSA health center sites",
            "definition": "Active HRSA service delivery and administrative/service delivery sites.",
            "source_id": "us_primary_care",
        },
        "pharmacy": {
            "label": "NPPES pharmacy organizations",
            "definition": "Active organization NPIs with the Community/Retail Pharmacy taxonomy and a primary practice location in the state.",
            "source_id": "us_pharmacies",
        },
    },
}

HWB_REGION_OVERRIDES = {
    "BRADFORD AND AIREDALE": "Yorkshire and the Humber",
    "DURHAM": "North East",
    "LEICESTER CITY": "East Midlands",
    "BRISTOL": "South West",
    "BOURNEMOUTH CHRISTCHURCH POOLE": "South West",
    "NORTHAMPTONSHIRE WEST": "East Midlands",
    "NORTHAMPTONSHIRE NORTH": "East Midlands",
    "NOTTINGHAM CITY": "East Midlands",
    "HULL": "Yorkshire and the Humber",
    "NEWCASTLE": "North East",
    "DERBY CITY": "East Midlands",
    "RICHMOND": "London",
    "KINGSTON": "London",
    "BEDFORD BOROUGH": "East of England",
    "HEREFORDSHIRE": "West Midlands",
    "BRACKNELL AND ASCOT": "South East",
}
PHARMACY_REGION_OVERRIDES_BY_ODS = {
    "FLD47": "East Midlands",
}

FACILITY_COLUMNS = [
    "country",
    "area_code",
    "category",
    "id",
    "name",
    "type",
    "address",
    "locality",
    "postal_code",
    "phone",
    "url",
    "latitude",
    "longitude",
    "weekly_hours",
    "sunday_hours",
    "emergency_services",
    "rating",
]


def _clean_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip(" ,")
    text = re.sub(r",(?=\S)", ", ", text)
    return text or None


def _normalise_url(value: object) -> str | None:
    url = _clean_text(value)
    if not url or url.lower() in {"none", "n/a", "na", "not available", "no website"}:
        return None
    if url.startswith("//"):
        return f"https:{url}"
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return f"https://{url}"
    return re.sub(r"^https?://", lambda match: match.group(0).lower(), url, flags=re.IGNORECASE)


def _normalise_us_postal(value: object) -> str | None:
    postal_code = _clean_text(value)
    if not postal_code:
        return None
    postal_code = re.sub(r"\.0$", "", postal_code)
    digits = re.sub(r"\D", "", postal_code)
    if len(digits) == 4:
        digits = digits.zfill(5)
    if len(digits) == 5:
        return digits
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    return postal_code


def _normalise_key(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(value).upper()).strip()


def _normalise_uk_region(value: object) -> str | None:
    region = _clean_text(value)
    if region == "East":
        return "East of England"
    if region == "Yorkshire & Humberside":
        return "Yorkshire and the Humber"
    return region if region in UK_REGION_NAME_TO_CODE else None


def _dedupe_pipe(value: object) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    parts = list(dict.fromkeys(part.strip() for part in text.split("|") if part.strip()))
    return " | ".join(parts)


def _address(*parts: object) -> str | None:
    cleaned = [text for part in parts if (text := _clean_text(part))]
    return ", ".join(cleaned) or None


def transform_uk_population(source_path: Path) -> pd.DataFrame:
    source = pd.read_excel(source_path, sheet_name="MYE2 - Persons", header=7)
    selected = source[source["Code"].isin(UK_REGION_CODES)].copy()
    output = pd.DataFrame(
        {
            "country": "UK",
            "area_code": selected["Code"],
            "area_name": selected["Code"].map(UK_REGION_CODES),
            "population": pd.to_numeric(selected["All ages"], errors="raise").astype(int),
            "population_year": 2024,
            "adult_population": pd.NA,
            "adult_population_year": pd.NA,
            "burden_adult_population": pd.NA,
            "burden_population_year": pd.NA,
        }
    )
    if set(output["area_code"]) != set(UK_REGION_CODES):
        raise ValueError("ONS population source does not contain all nine English regions")
    return output.sort_values("area_code").reset_index(drop=True)


def transform_us_population(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, encoding="latin1", low_memory=False)
    source["area_code"] = source["STATE"].map(US_STATE_FIPS_TO_CODE)
    selected = source[
        source["area_code"].notna()
        & source["SUMLEV"].eq(40)
        & source["SEX"].eq(0)
        & source["ORIGIN"].eq(0)
    ].copy()
    rows: list[dict[str, object]] = []
    for area_code, state_rows in selected.groupby("area_code"):
        rows.append(
            {
                "country": "USA",
                "area_code": area_code,
                "area_name": US_STATE_NAMES[str(area_code)],
                "population": int(state_rows["POPESTIMATE2025"].sum()),
                "population_year": 2025,
                "adult_population": int(
                    state_rows.loc[state_rows["AGE"].ge(18), "POPESTIMATE2025"].sum()
                ),
                "adult_population_year": 2025,
                "burden_adult_population": int(
                    state_rows.loc[state_rows["AGE"].ge(18), "POPESTIMATE2023"].sum()
                ),
                "burden_population_year": 2023,
            }
        )
    output = pd.DataFrame(rows)
    if set(output["area_code"]) != set(US_STATE_NAMES):
        raise ValueError("Census source does not contain all 50 states and District of Columbia")
    return output.sort_values("area_code").reset_index(drop=True)


def _cqc_base(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, skiprows=4, dtype=str, low_memory=False)
    source["region_name"] = source["Region"].map(_normalise_uk_region)
    source["area_code"] = source["region_name"].map(UK_REGION_NAME_TO_CODE)
    return source[source["area_code"].notna()].copy()


def transform_uk_cqc_facilities(source_path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    source = _cqc_base(source_path)
    authority_region = (
        source.dropna(subset=["Local authority", "region_name"])
        .assign(authority_key=lambda frame: frame["Local authority"].map(_normalise_key))
        .groupby("authority_key")["region_name"]
        .agg(lambda values: values.mode().iloc[0])
        .to_dict()
    )
    frames: list[pd.DataFrame] = []
    service_types = source["Service types"].fillna("").map(
        lambda value: {part.strip() for part in value.split("|") if part.strip()}
    )
    category_masks = {
        "hospital": service_types.map(
            lambda values: bool(values & {"Hospital", "Hospitals - Mental health/capacity"})
        ),
        "primary_care": service_types.map(lambda values: "Doctors/GPs" in values),
    }
    for category, mask in category_masks.items():
        selected = source[mask].copy()
        frame = pd.DataFrame(
            {
                "country": "UK",
                "area_code": selected["area_code"],
                "category": category,
                "id": selected["CQC Location ID (for office use only)"],
                "name": selected["Name"].map(_clean_text),
                "type": selected["Service types"].map(_dedupe_pipe),
                "address": selected["Address"].map(_clean_text),
                "locality": selected["Local authority"].map(_clean_text),
                "postal_code": selected["Postcode"].map(_clean_text),
                "phone": selected["Phone number"].map(_clean_text),
                "url": selected["Location URL"].map(_clean_text),
            }
        )
        frames.append(frame)
    facilities = pd.concat(frames, ignore_index=True)
    return _complete_facility_columns(facilities), authority_region


def transform_uk_pharmacies(
    source_path: Path,
    authority_region: dict[str, str],
) -> pd.DataFrame:
    source = pd.read_csv(source_path, low_memory=False)
    selected = source[source["CONTRACT_TYPE"].isin(["Community", "LPS"])].copy()
    selected["authority_key"] = selected["HEALTH_AND_WELLBEING_BOARD"].map(_normalise_key)
    selected["region_name"] = selected["authority_key"].map(authority_region)
    selected["region_name"] = selected["region_name"].fillna(
        selected["authority_key"].map(HWB_REGION_OVERRIDES)
    )
    selected["region_name"] = selected["region_name"].fillna(
        selected["PHARMACY_ODS_CODE_F_CODE"].map(PHARMACY_REGION_OVERRIDES_BY_ODS)
    )
    if selected["region_name"].isna().any():
        missing = sorted(selected.loc[selected["region_name"].isna(), "HEALTH_AND_WELLBEING_BOARD"].unique())
        raise ValueError(f"Unmapped NHSBSA Health and Wellbeing Boards: {missing}")
    frame = pd.DataFrame(
        {
            "country": "UK",
            "area_code": selected["region_name"].map(UK_REGION_NAME_TO_CODE),
            "category": "pharmacy",
            "id": selected["PHARMACY_ODS_CODE_F_CODE"],
            "name": selected["PHARMACY_TRADING_NAME"].map(_clean_text),
            "type": selected["CONTRACT_TYPE"].map(
                {"Community": "Community pharmacy", "LPS": "Local Pharmaceutical Services"}
            ),
            "address": selected.apply(
                lambda row: _address(
                    row["ADDRESS_FIELD_1"],
                    row["ADDRESS_FIELD_2"],
                    row["ADDRESS_FIELD_3"],
                    row["ADDRESS_FIELD_4"],
                ),
                axis=1,
            ),
            "locality": selected["HEALTH_AND_WELLBEING_BOARD"].map(_clean_text),
            "postal_code": selected["POST_CODE"].map(_clean_text),
            "phone": None,
            "url": ACCESS_SOURCES["uk_pharmacies"]["url"],
            "weekly_hours": pd.to_numeric(selected["WEEKLY_TOTAL"], errors="coerce"),
            "sunday_hours": pd.to_numeric(selected["SUN_TOTAL"], errors="coerce"),
        }
    )
    return _complete_facility_columns(frame)


def transform_us_hospitals(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, dtype=str, low_memory=False)
    selected = source[source["State"].isin(US_STATE_NAMES)].copy()
    frame = pd.DataFrame(
        {
            "country": "USA",
            "area_code": selected["State"],
            "category": "hospital",
            "id": selected["Facility ID"],
            "name": selected["Facility Name"].map(_clean_text),
            "type": selected["Hospital Type"].map(_clean_text),
            "address": selected["Address"].map(_clean_text),
            "locality": selected["City/Town"].map(_clean_text),
            "postal_code": selected["ZIP Code"].map(_normalise_us_postal),
            "phone": selected["Telephone Number"].map(_clean_text),
            "url": ACCESS_SOURCES["us_hospitals"]["url"],
            "emergency_services": selected["Emergency Services"].map(_clean_text),
            "rating": pd.to_numeric(selected["Hospital overall rating"], errors="coerce"),
        }
    )
    return _complete_facility_columns(frame)


def transform_us_health_centers(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, low_memory=False)
    selected = source[
        source["Site State Abbreviation"].isin(US_STATE_NAMES)
        & source["Site Status Description"].eq("Active")
        & ~source["Health Center Type Description"].eq("Administrative")
    ].copy()
    frame = pd.DataFrame(
        {
            "country": "USA",
            "area_code": selected["Site State Abbreviation"],
            "category": "primary_care",
            "id": selected["BPHC Assigned Number"],
            "name": selected["Site Name"].map(_clean_text),
            "type": selected["Health Center Type Description"].map(_clean_text),
            "address": selected["Site Address"].map(_clean_text),
            "locality": selected["Site City"].map(_clean_text),
            "postal_code": selected["Site Postal Code"].map(_normalise_us_postal),
            "phone": selected["Site Telephone Number"].map(_clean_text),
            "url": selected["Site Web Address"].map(_normalise_url),
            "latitude": pd.to_numeric(
                selected["Geocoding Artifact Address Primary Y Coordinate"], errors="coerce"
            ),
            "longitude": pd.to_numeric(
                selected["Geocoding Artifact Address Primary X Coordinate"], errors="coerce"
            ),
            "weekly_hours": pd.to_numeric(selected["Operating Hours per Week"], errors="coerce"),
        }
    )
    return _complete_facility_columns(frame)


def transform_us_pharmacies(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, dtype=str, low_memory=False)
    required = {"npi", "name", "address", "city", "state", "postal_code", "phone"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"NPPES pharmacy extract is missing columns: {sorted(missing)}")
    selected = source[source["state"].isin(US_STATE_NAMES)].copy()
    selected["display_name"] = selected.apply(
        lambda row: _clean_text(row["name"]) or f"NPI organization {row['npi']}",
        axis=1,
    )
    frame = pd.DataFrame(
        {
            "country": "USA",
            "area_code": selected["state"],
            "category": "pharmacy",
            "id": selected["npi"],
            "name": selected["display_name"],
            "type": "Community/Retail Pharmacy",
            "address": selected["address"].map(_clean_text),
            "locality": selected["city"].map(_clean_text),
            "postal_code": selected["postal_code"].map(_normalise_us_postal),
            "phone": selected["phone"].map(_clean_text),
            "url": selected["npi"].map(
                lambda npi: f"https://npiregistry.cms.hhs.gov/provider-view/{npi}"
            ),
        }
    )
    return _complete_facility_columns(frame)


def transform_us_hpsa(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, dtype={"HPSA ID": str}, low_memory=False)
    selected = source[
        source["Primary State Abbreviation"].isin(US_STATE_NAMES)
        & source["HPSA Status"].eq("Designated")
    ].drop_duplicates(["Primary State Abbreviation", "HPSA ID"])
    selected["HPSA Shortage"] = pd.to_numeric(selected["HPSA Shortage"], errors="coerce")
    selected["HPSA Score"] = pd.to_numeric(selected["HPSA Score"], errors="coerce")
    grouped = selected.groupby("Primary State Abbreviation")
    output = grouped.agg(
        hpsa_designation_count=("HPSA ID", "nunique"),
        hpsa_fte_shortage=("HPSA Shortage", "sum"),
        hpsa_score_median=("HPSA Score", "median"),
    ).reset_index().rename(columns={"Primary State Abbreviation": "area_code"})
    output["country"] = "USA"
    return output[[
        "country",
        "area_code",
        "hpsa_designation_count",
        "hpsa_fte_shortage",
        "hpsa_score_median",
    ]]


def _complete_facility_columns(frame: pd.DataFrame) -> pd.DataFrame:
    completed = frame.copy()
    for column in FACILITY_COLUMNS:
        if column not in completed:
            completed[column] = None
    completed = completed[FACILITY_COLUMNS]
    completed["id"] = completed["id"].astype(str)
    return completed.sort_values(["country", "area_code", "category", "name", "id"]).reset_index(drop=True)


def build_access_summary(
    populations: pd.DataFrame,
    facilities: pd.DataFrame,
    hpsa: pd.DataFrame,
) -> pd.DataFrame:
    counts = (
        facilities.groupby(["country", "area_code", "category"])["id"]
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )
    summary = populations.merge(counts, on=["country", "area_code"], how="left")
    for category in ("hospital", "primary_care", "pharmacy"):
        if category not in summary:
            summary[category] = 0
        summary[f"{category}_count"] = summary.pop(category).fillna(0).astype(int)
        summary[f"{category}_per_100k"] = (
            summary[f"{category}_count"] / summary["population"] * 100_000
        ).round(2)

    pharmacy = facilities[facilities["category"].eq("pharmacy")].copy()
    pharmacy["open_sunday"] = pd.to_numeric(pharmacy["sunday_hours"], errors="coerce").gt(0)
    sunday = pharmacy[pharmacy["country"].eq("UK")].groupby("area_code").agg(
        pharmacy_sunday_open_pct=("open_sunday", lambda values: round(values.mean() * 100, 1)),
        pharmacy_median_weekly_hours=("weekly_hours", "median"),
    )
    hospitals = facilities[
        facilities["country"].eq("USA") & facilities["category"].eq("hospital")
    ].copy()
    hospitals["has_emergency"] = hospitals["emergency_services"].eq("Yes")
    emergency = hospitals.groupby("area_code").agg(
        hospital_emergency_pct=("has_emergency", lambda values: round(values.mean() * 100, 1)),
    )
    primary = facilities[
        facilities["country"].eq("USA") & facilities["category"].eq("primary_care")
    ]
    primary_hours = primary.groupby("area_code").agg(
        primary_care_median_weekly_hours=("weekly_hours", "median"),
    )
    summary = summary.merge(sunday, on="area_code", how="left")
    summary = summary.merge(emergency, on="area_code", how="left")
    summary = summary.merge(primary_hours, on="area_code", how="left")
    summary = summary.merge(hpsa, on=["country", "area_code"], how="left")
    return summary.sort_values(["country", "area_code"]).reset_index(drop=True)


def _json_record(row: pd.Series) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for column in FACILITY_COLUMNS:
        if column in {"country", "area_code", "category"}:
            continue
        value = row[column]
        if pd.isna(value) or value is None or value == "":
            continue
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        record[column] = value
    return record


def write_facility_payloads(
    facilities: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: Path,
) -> None:
    for _, area in summary.iterrows():
        country = str(area["country"])
        area_code = str(area["area_code"])
        area_facilities = facilities[
            facilities["country"].eq(country) & facilities["area_code"].eq(area_code)
        ]
        categories: dict[str, object] = {}
        for category in ("hospital", "primary_care", "pharmacy"):
            definitions = FACILITY_DEFINITIONS[country][category]
            source = ACCESS_SOURCES[definitions["source_id"]]
            rows = area_facilities[area_facilities["category"].eq(category)]
            categories[category] = {
                "label": definitions["label"],
                "definition": definitions["definition"],
                "source_name": source["name"],
                "source_url": source["url"],
                "source_period": source["period"],
                "records": [_json_record(row) for _, row in rows.iterrows()],
            }
        payload = {
            "country": country,
            "area_code": area_code,
            "area_name": area["area_name"],
            "categories": categories,
        }
        destination = output_dir / country.lower() / f"{area_code.lower()}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )


def enrich_dashboard_payload(
    dashboard_json: Path,
    summary: pd.DataFrame,
    *,
    extract_date: str,
) -> None:
    payload = json.loads(dashboard_json.read_text(encoding="utf-8"))
    indexed = summary.set_index(["country", "area_code"])
    for country_code, country in payload["countries"].items():
        country_rows = summary[summary["country"].eq(country_code)]
        peer_medians = {
            category: float(country_rows[f"{category}_per_100k"].median())
            for category in ("hospital", "primary_care", "pharmacy")
        }
        for entity in country["entities"]:
            area_code = str(entity["area_code"])
            row = indexed.loc[(country_code, area_code)]
            capacity = []
            for category in ("hospital", "primary_care", "pharmacy"):
                definition = FACILITY_DEFINITIONS[country_code][category]
                source = ACCESS_SOURCES[definition["source_id"]]
                capacity.append(
                    {
                        "key": category,
                        "label": definition["label"],
                        "definition": definition["definition"],
                        "count": int(row[f"{category}_count"]),
                        "per_100k": row[f"{category}_per_100k"],
                        "peer_median_per_100k": round(peer_medians[category], 2),
                        "source_name": source["name"],
                        "source_url": source["url"],
                        "source_period": source["period"],
                    }
                )
            access: dict[str, object] = {
                "population": {
                    "value": int(row["population"]),
                    "year": int(row["population_year"]),
                    "adult_value": None if pd.isna(row["adult_population"]) else int(row["adult_population"]),
                    "adult_year": None if pd.isna(row["adult_population_year"]) else int(row["adult_population_year"]),
                    "source_name": ACCESS_SOURCES["uk_population" if country_code == "UK" else "us_population"]["name"],
                    "source_url": ACCESS_SOURCES["uk_population" if country_code == "UK" else "us_population"]["url"],
                },
                "capacity": capacity,
                "facility_file": f"assets/facilities/{country_code.lower()}/{area_code.lower()}.json",
            }
            if country_code == "UK":
                access["operating_context"] = {
                    "label": "Sunday-opening pharmacy share",
                    "value": None if pd.isna(row["pharmacy_sunday_open_pct"]) else row["pharmacy_sunday_open_pct"],
                    "unit": "%",
                    "detail": "Share of listed community/LPS pharmacy sites with Sunday hours.",
                }
            else:
                access["operating_context"] = {
                    "label": "Hospitals with emergency services",
                    "value": None if pd.isna(row["hospital_emergency_pct"]) else row["hospital_emergency_pct"],
                    "unit": "%",
                    "detail": "Share of CMS-listed hospitals reporting emergency services.",
                }
                access["shortage"] = {
                    "designation_count": int(row["hpsa_designation_count"]),
                    "fte_shortage": round(float(row["hpsa_fte_shortage"]), 1),
                    "median_score": round(float(row["hpsa_score_median"]), 1),
                    "source_name": ACCESS_SOURCES["us_shortage"]["name"],
                    "source_url": ACCESS_SOURCES["us_shortage"]["url"],
                    "source_period": ACCESS_SOURCES["us_shortage"]["period"],
                }
            entity["access"] = access
            _add_metric_burden(entity, row, country_code)

    known_sources = {source["id"] for source in payload["sources"]}
    for source_id, source in ACCESS_SOURCES.items():
        if source_id not in known_sources:
            payload["sources"].append({"id": source_id, **source})
    payload["meta"]["extract_date"] = extract_date
    payload["meta"]["data_boundary"] = (
        "Official aggregate health data and public facility directory records; "
        "no patient-level or person-level records."
    )
    payload["meta"]["access_boundary"] = (
        "Facility directories and density measures describe listed records, not licensure, "
        "travel time, appointment availability, service quality or a determination of adequacy."
    )
    dashboard_json.write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _add_metric_burden(entity: dict[str, Any], row: pd.Series, country_code: str) -> None:
    for metric in entity["metrics"].values():
        if country_code == "UK":
            numerator = metric.get("latest_numerator")
            denominator = metric.get("latest_denominator")
            if numerator is None or denominator is None:
                continue
            metric["burden"] = {
                "kind": "recorded",
                "label": "Recorded disease register",
                "value": int(round(float(numerator))),
                "lower": None,
                "upper": None,
                "denominator": int(round(float(denominator))),
                "denominator_label": metric["population"],
                "population_year": metric["latest_period"],
                "prevalence": metric["latest_value"],
                "note": "Official QOF register count and metric-specific registered-patient denominator.",
            }
            continue

        crude_value = metric.get("latest_crude_value")
        crude_lower = metric.get("latest_crude_lower_ci")
        crude_upper = metric.get("latest_crude_upper_ci")
        if crude_value is None or pd.isna(crude_value):
            continue
        adult_population = int(row["burden_adult_population"])
        metric["burden"] = {
            "kind": "modelled",
            "label": "Estimated adults",
            "value": int(round(adult_population * float(crude_value) / 100)),
            "lower": None if pd.isna(crude_lower) else int(round(adult_population * float(crude_lower) / 100)),
            "upper": None if pd.isna(crude_upper) else int(round(adult_population * float(crude_upper) / 100)),
            "denominator": adult_population,
            "denominator_label": "Census resident population aged 18+",
            "population_year": int(row["burden_population_year"]),
            "prevalence": float(crude_value),
            "prevalence_lower": None if pd.isna(crude_lower) else float(crude_lower),
            "prevalence_upper": None if pd.isna(crude_upper) else float(crude_upper),
            "note": "Planning estimate: CDC crude prevalence multiplied by the same-year Census adult population; not a case count.",
        }


def source_inventory(facilities: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for country, definitions in FACILITY_DEFINITIONS.items():
        for category, definition in definitions.items():
            source = ACCESS_SOURCES[definition["source_id"]]
            count = facilities[
                facilities["country"].eq(country) & facilities["category"].eq(category)
            ]["id"].nunique()
            rows.append(
                {
                    "country": country,
                    "category": category,
                    "definition": definition["definition"],
                    "record_count": count,
                    "source_name": source["name"],
                    "source_period": source["period"],
                    "source_url": source["url"],
                }
            )
    return pd.DataFrame(rows)
