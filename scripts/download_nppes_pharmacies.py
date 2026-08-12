"""Create a compact state-level pharmacy organization extract from NPPES.

Only active organization NPIs with taxonomy code 3336C0003X and a matching
location address are retained. Authorized-official fields are not exported.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from pathlib import Path
import time

import requests


API_URL = "https://npiregistry.cms.hhs.gov/api/"
TAXONOMY_CODE = "3336C0003X"
STATE_CODES = "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()


def _prefix_range(start: int, end: int) -> list[str]:
    return [f"{value:02d}" for value in range(start, end + 1)]


STATE_ZIP2_PREFIXES = {
    "AL": _prefix_range(35, 36), "AK": ["99"], "AZ": ["85", "86"],
    "AR": ["71", "72", "75"], "CA": _prefix_range(90, 96),
    "CO": ["80", "81"], "CT": ["06"], "DE": ["19"], "DC": ["20", "56"],
    "FL": _prefix_range(32, 34), "GA": ["30", "31", "39"], "HI": ["96"],
    "ID": ["83"], "IL": _prefix_range(60, 62), "IN": ["46", "47"],
    "IA": _prefix_range(50, 52), "KS": ["66", "67"],
    "KY": _prefix_range(40, 42), "LA": ["70", "71"], "ME": ["03", "04"],
    "MD": ["20", "21"], "MA": ["01", "02", "05"], "MI": ["48", "49"],
    "MN": ["55", "56"], "MS": ["38", "39"], "MO": _prefix_range(63, 65),
    "MT": ["59"], "NE": ["68", "69"], "NV": ["88", "89"], "NH": ["03"],
    "NJ": ["07", "08"], "NM": ["87", "88"],
    "NY": ["00", "06", *_prefix_range(9, 14)], "NC": ["27", "28"],
    "ND": ["58"], "OH": _prefix_range(43, 45), "OK": ["73", "74"],
    "OR": ["97"], "PA": _prefix_range(15, 19), "RI": ["02"], "SC": ["29"],
    "SD": ["57"], "TN": ["37", "38"],
    "TX": ["73", *_prefix_range(75, 79), "88"], "UT": ["84"], "VT": ["05"],
    "VA": ["20", "22", "23", "24"], "WA": ["98", "99"],
    "WV": ["24", "25", "26"], "WI": ["53", "54"], "WY": ["82", "83"],
}
FIELDNAMES = [
    "npi",
    "name",
    "address",
    "city",
    "state",
    "postal_code",
    "phone",
    "enumeration_date",
    "last_updated",
    "snapshot_date",
]


def _request_json(parameters: dict[str, object], retries: int = 4) -> dict[str, object]:
    for attempt in range(retries):
        try:
            response = requests.get(
                API_URL,
                params=parameters,
                headers={"User-Agent": "regional-health-risk-ai/1.0"},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt + 1 == retries:
                raise
            time.sleep(1.5 * (2**attempt))
    raise RuntimeError("NPPES request failed")


def _location_address(result: dict[str, object], state: str) -> dict[str, object] | None:
    addresses = result.get("addresses") or []
    for address in addresses:
        if address.get("address_purpose") == "LOCATION" and address.get("state") == state:
            return address
    return None


def _pharmacy_record(
    result: dict[str, object],
    state: str,
    snapshot_date: str,
) -> dict[str, str] | None:
    basic = result.get("basic") or {}
    if basic.get("status") != "A":
        return None
    taxonomies = result.get("taxonomies") or []
    if not any(taxonomy.get("code") == TAXONOMY_CODE for taxonomy in taxonomies):
        return None
    location = _location_address(result, state)
    if location is None:
        return None
    return {
        "npi": str(result.get("number") or ""),
        "name": str(basic.get("organization_name") or "").strip(),
        "address": " ".join(
            str(location.get(field) or "").strip()
            for field in ("address_1", "address_2")
            if str(location.get(field) or "").strip()
        ),
        "city": str(location.get("city") or "").strip(),
        "state": state,
        "postal_code": str(location.get("postal_code") or "").strip(),
        "phone": str(location.get("telephone_number") or "").strip(),
        "enumeration_date": str(basic.get("enumeration_date") or "").strip(),
        "last_updated": str(basic.get("last_updated") or "").strip(),
        "snapshot_date": snapshot_date,
    }


def _fetch_partition(
    state: str,
    snapshot_date: str,
    *,
    postal_prefix: str | None,
    page_size: int,
) -> tuple[list[dict[str, str]], bool]:
    records: dict[str, dict[str, str]] = {}
    for page in range(6):
        parameters: dict[str, object] = {
            "version": "2.1",
            "enumeration_type": "NPI-2",
            "taxonomy_description": "Community/Retail Pharmacy",
            "address_purpose": "PRIMARY",
            "state": state,
            "limit": page_size,
            "skip": page * page_size,
        }
        if postal_prefix is not None:
            parameters["postal_code"] = f"{postal_prefix}*"
        payload = _request_json(
            parameters
        )
        results = payload.get("results") or []
        if not results:
            return list(records.values()), False
        for result in results:
            record = _pharmacy_record(result, state, snapshot_date)
            if record and record["npi"]:
                records[record["npi"]] = record
        if len(results) < page_size:
            return list(records.values()), False
    return list(records.values()), True


def _fetch_prefix(
    state: str,
    prefix: str,
    snapshot_date: str,
    page_size: int,
) -> list[dict[str, str]]:
    records, capped = _fetch_partition(
        state,
        snapshot_date,
        postal_prefix=prefix,
        page_size=page_size,
    )
    if not capped:
        return records
    if len(prefix) >= 5:
        raise RuntimeError(f"NPPES partition remains capped for {state} ZIP prefix {prefix}")
    split_records: list[dict[str, str]] = []
    for digit in "0123456789":
        split_records.extend(_fetch_prefix(state, f"{prefix}{digit}", snapshot_date, page_size))
    return split_records


def fetch_state(state: str, snapshot_date: str, page_size: int = 200) -> list[dict[str, str]]:
    records, capped = _fetch_partition(
        state,
        snapshot_date,
        postal_prefix=None,
        page_size=page_size,
    )
    if capped:
        records = []
        for prefix in STATE_ZIP2_PREFIXES[state]:
            records.extend(_fetch_prefix(state, prefix, snapshot_date, page_size))
    records = {record["npi"]: record for record in records}
    return sorted(records.values(), key=lambda row: (row["name"], row["npi"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-date", default="2026-08-13")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--states", nargs="*", default=STATE_CODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    invalid = sorted(set(args.states) - set(STATE_CODES))
    if invalid:
        raise ValueError(f"Unsupported state codes: {invalid}")
    rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(fetch_state, state, args.snapshot_date): state
            for state in args.states
        }
        for future in as_completed(futures):
            state = futures[future]
            state_rows = future.result()
            rows.extend(state_rows)
            print(f"{state}: {len(state_rows):,} active community/retail pharmacy organizations")

    rows.sort(key=lambda row: (row["state"], row["name"], row["npi"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} records to {args.output}")


if __name__ == "__main__":
    main()
