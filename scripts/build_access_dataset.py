"""Build population, healthcare-capacity and facility-directory snapshots.

The script reads locally downloaded public source files and enriches the static
dashboard payload produced by ``build_regional_dataset.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.access_data import (
    build_access_summary,
    enrich_dashboard_payload,
    source_inventory,
    transform_uk_cqc_facilities,
    transform_uk_pharmacies,
    transform_uk_population,
    transform_us_health_centers,
    transform_us_hospitals,
    transform_us_hpsa,
    transform_us_pharmacies,
    transform_us_population,
    write_facility_payloads,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uk-population", type=Path, required=True)
    parser.add_argument("--uk-cqc-directory", type=Path, required=True)
    parser.add_argument("--uk-pharmacies", type=Path, required=True)
    parser.add_argument("--us-population", type=Path, required=True)
    parser.add_argument("--us-hospitals", type=Path, required=True)
    parser.add_argument("--us-health-centers", type=Path, required=True)
    parser.add_argument("--us-pharmacies", type=Path, required=True)
    parser.add_argument("--us-hpsa", type=Path, required=True)
    parser.add_argument(
        "--dashboard-json",
        type=Path,
        default=Path("docs/assets/regional_data.json"),
    )
    parser.add_argument(
        "--facility-output-dir",
        type=Path,
        default=Path("docs/assets/facilities"),
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("data/official/regional_access_summary.csv"),
    )
    parser.add_argument(
        "--source-inventory-csv",
        type=Path,
        default=Path("data/official/access_source_inventory.csv"),
    )
    parser.add_argument("--extract-date", default="2026-08-13")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uk_population = transform_uk_population(args.uk_population)
    us_population = transform_us_population(args.us_population)
    uk_cqc, authority_region = transform_uk_cqc_facilities(args.uk_cqc_directory)
    uk_pharmacies = transform_uk_pharmacies(args.uk_pharmacies, authority_region)
    us_hospitals = transform_us_hospitals(args.us_hospitals)
    us_health_centers = transform_us_health_centers(args.us_health_centers)
    us_pharmacies = transform_us_pharmacies(args.us_pharmacies)
    hpsa = transform_us_hpsa(args.us_hpsa)

    facilities = pd.concat(
        [uk_cqc, uk_pharmacies, us_hospitals, us_health_centers, us_pharmacies],
        ignore_index=True,
    )
    populations = pd.concat([uk_population, us_population], ignore_index=True)
    summary = build_access_summary(populations, facilities, hpsa)

    args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_csv, index=False)
    inventory = source_inventory(facilities)
    args.source_inventory_csv.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(args.source_inventory_csv, index=False)
    write_facility_payloads(facilities, summary, args.facility_output_dir)
    enrich_dashboard_payload(
        args.dashboard_json,
        summary,
        extract_date=args.extract_date,
    )


if __name__ == "__main__":
    main()
