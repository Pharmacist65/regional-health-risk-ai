"""Local open-data mapping helpers for aggregate public-health analytics.

The functions in this module convert downloaded aggregate CSV-style extracts
into the project's internal schemas. They do not make live API calls, require
API keys, or handle patient-level data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping
import re

import pandas as pd

from src.validation import (
    PRESCRIBING_REQUIRED_COLUMNS,
    PUBLIC_HEALTH_REQUIRED_COLUMNS,
    SUPPORTED_MEDICATION_CLASSES,
    validate_prescribing_data,
    validate_public_health_data,
)


CsvSource = str | Path | pd.DataFrame

OPENPRESCRIBING_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "month": ("month", "period", "date"),
    "area_code": ("area_code", "org_code", "organisation_code", "practice_code", "ccg_code"),
    "area_name": ("area_name", "org_name", "organisation_name", "practice_name", "ccg_name"),
    "medication_class": ("medication_class", "measure_name", "bnf_section", "bnf_name"),
    "items_per_1000": (
        "items_per_1000",
        "items_per_1000_patients",
        "items_rate_per_1000",
        "numerator_per_1000",
    ),
    "cost_per_1000": (
        "cost_per_1000",
        "actual_cost_per_1000",
        "cost_rate_per_1000",
        "nic_per_1000",
    ),
}

OHID_LONG_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "area_code": ("area_code", "area code", "Area Code"),
    "area_name": ("area_name", "area name", "Area Name"),
    "indicator_name": ("indicator_name", "indicator name", "Indicator Name"),
    "indicator_value": ("indicator_value", "value", "Value"),
}

AREA_METADATA_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "area_code": ("area_code", "area code", "Area Code"),
    "area_name": ("area_name", "area name", "Area Name"),
    "latitude": ("latitude", "lat", "Latitude"),
    "longitude": ("longitude", "lon", "lng", "Longitude"),
}

DEFAULT_MEDICATION_CLASS_MAP: dict[str, str] = {
    "nsaid": "NSAID",
    "nsaids": "NSAID",
    "nonsteroidalantiinflammatorydrugs": "NSAID",
    "nonsteroidalantiinflammatorydrug": "NSAID",
    "antihypertensive": "Antihypertensive",
    "antihypertensives": "Antihypertensive",
    "lipidlowering": "Lipid-lowering",
    "lipidloweringdrugs": "Lipid-lowering",
    "lipidmodifyingdrugs": "Lipid-lowering",
    "statins": "Lipid-lowering",
    "antidiabetic": "Antidiabetic",
    "antidiabetics": "Antidiabetic",
    "drugsusedindiabetes": "Antidiabetic",
}

DEFAULT_OHID_INDICATOR_MAP: dict[str, str] = {
    "saturatedfatproxyindex": "saturated_fat_proxy_index",
    "deprivationindex": "deprivation_index",
    "obesityprevalence": "obesity_prevalence_pct",
    "obesityprevalencepct": "obesity_prevalence_pct",
    "obesityprevalencepercentage": "obesity_prevalence_pct",
    "hypertensionprevalenceestimate": "hypertension_prevalence_estimate_pct",
    "hypertensionprevalenceestimatepct": "hypertension_prevalence_estimate_pct",
    "diabetesprevalenceestimate": "diabetes_prevalence_estimate_pct",
    "diabetesprevalenceestimatepct": "diabetes_prevalence_estimate_pct",
}


def _canonical_label(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _read_csv_source(source: CsvSource) -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        return source.copy()
    return pd.read_csv(Path(source))


def _column_lookup(df: pd.DataFrame) -> dict[str, str]:
    return {_canonical_label(column): column for column in df.columns}


def _resolve_column(
    df: pd.DataFrame,
    target_column: str,
    aliases: Mapping[str, tuple[str, ...]],
    column_map: Mapping[str, str] | None,
) -> str | None:
    lookup = _column_lookup(df)
    explicit_source = column_map.get(target_column) if column_map else None
    candidates = (explicit_source,) if explicit_source else aliases.get(target_column, ())
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = lookup.get(_canonical_label(candidate))
        if resolved is not None:
            return resolved
    return None


def _rename_columns_for_schema(
    df: pd.DataFrame,
    required_columns: tuple[str, ...],
    aliases: Mapping[str, tuple[str, ...]],
    *,
    column_map: Mapping[str, str] | None,
    source_name: str,
) -> pd.DataFrame:
    resolved_columns = {
        target: _resolve_column(df, target, aliases, column_map)
        for target in required_columns
    }
    missing = [target for target, source in resolved_columns.items() if source is None]
    if missing:
        raise ValueError(
            f"{source_name} source is missing required source columns for: {missing}"
        )

    renamed = df[[resolved_columns[target] for target in required_columns]].copy()
    renamed.columns = list(required_columns)
    return renamed


def _normalise_month_start(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.to_period("M").dt.to_timestamp().dt.strftime("%Y-%m-%d")


def _normalised_value_map(defaults: Mapping[str, str], overrides: Mapping[str, str] | None) -> dict[str, str]:
    value_map = dict(defaults)
    if overrides:
        value_map.update({_canonical_label(source): target for source, target in overrides.items()})
    return value_map


def map_openprescribing_aggregate_csv(
    source: CsvSource,
    *,
    column_map: Mapping[str, str] | None = None,
    medication_class_map: Mapping[str, str] | None = None,
    aggregate_duplicate_rows: bool = True,
) -> pd.DataFrame:
    """Map a local OpenPrescribing-style aggregate extract to project schema.

    Parameters
    ----------
    source:
        Local CSV path or in-memory dataframe. The source must be aggregate and
        area-level.
    column_map:
        Optional mapping from project column names to source column names.
    medication_class_map:
        Optional mapping from source medication labels to one of the supported
        project classes.
    aggregate_duplicate_rows:
        If true, rows that map to the same month, area and medication class are
        summed. This is useful when a downloaded extract contains multiple
        low-level aggregate rows for a single project medication class.
    """
    source_df = _read_csv_source(source)
    mapped = _rename_columns_for_schema(
        source_df,
        PRESCRIBING_REQUIRED_COLUMNS,
        OPENPRESCRIBING_COLUMN_ALIASES,
        column_map=column_map,
        source_name="OpenPrescribing-style prescribing",
    )

    class_map = _normalised_value_map(DEFAULT_MEDICATION_CLASS_MAP, medication_class_map)
    for medication_class in SUPPORTED_MEDICATION_CLASSES:
        class_map[_canonical_label(medication_class)] = medication_class

    mapped["month"] = _normalise_month_start(mapped["month"])
    mapped["medication_class"] = (
        mapped["medication_class"]
        .astype(str)
        .str.strip()
        .map(lambda value: class_map.get(_canonical_label(value), value))
    )
    mapped["items_per_1000"] = pd.to_numeric(mapped["items_per_1000"], errors="coerce")
    mapped["cost_per_1000"] = pd.to_numeric(mapped["cost_per_1000"], errors="coerce")

    if aggregate_duplicate_rows:
        mapped = (
            mapped.groupby(
                ["month", "area_code", "area_name", "medication_class"],
                as_index=False,
                dropna=False,
            )
            .agg(
                items_per_1000=("items_per_1000", lambda series: series.sum(min_count=1)),
                cost_per_1000=("cost_per_1000", lambda series: series.sum(min_count=1)),
            )
        )

    mapped = mapped.loc[:, PRESCRIBING_REQUIRED_COLUMNS]
    validate_prescribing_data(mapped)
    return mapped


def _map_indicator_name(value: object, indicator_map: Mapping[str, str]) -> str | None:
    return indicator_map.get(_canonical_label(value))


def map_ohid_fingertips_indicator_csv(
    source: CsvSource,
    *,
    indicator_map: Mapping[str, str] | None = None,
    column_map: Mapping[str, str] | None = None,
    area_metadata: CsvSource | None = None,
    metadata_column_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Map a local OHID/Fingertips-style long indicator extract to project schema.

    The source is expected to contain one aggregate indicator value per area and
    indicator. Latitude and longitude can be included in the same file or
    supplied separately through ``area_metadata``.
    """
    source_df = _read_csv_source(source)
    long_df = _rename_columns_for_schema(
        source_df,
        ("area_code", "area_name", "indicator_name", "indicator_value"),
        OHID_LONG_COLUMN_ALIASES,
        column_map=column_map,
        source_name="OHID/Fingertips-style indicator",
    )

    resolved_indicator_map = _normalised_value_map(DEFAULT_OHID_INDICATOR_MAP, indicator_map)
    long_df["target_indicator"] = long_df["indicator_name"].map(
        lambda value: _map_indicator_name(value, resolved_indicator_map)
    )
    mapped_indicators = long_df[long_df["target_indicator"].notna()].copy()
    if mapped_indicators.empty:
        raise ValueError("No OHID/Fingertips indicators matched the project indicator map.")

    duplicate_indicator_rows = mapped_indicators.duplicated(
        subset=["area_code", "area_name", "target_indicator"],
        keep=False,
    )
    if duplicate_indicator_rows.any():
        raise ValueError(
            "Duplicate OHID/Fingertips source rows found for area and mapped indicator. "
            "Filter the source to one period or aggregate it before mapping."
        )

    mapped_indicators["indicator_value"] = pd.to_numeric(
        mapped_indicators["indicator_value"],
        errors="coerce",
    )
    indicator_wide = (
        mapped_indicators.pivot(
            index=["area_code", "area_name"],
            columns="target_indicator",
            values="indicator_value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    metadata_source = _read_csv_source(area_metadata) if area_metadata is not None else source_df
    area_columns = _rename_columns_for_schema(
        metadata_source,
        ("area_code", "area_name", "latitude", "longitude"),
        AREA_METADATA_COLUMN_ALIASES,
        column_map=metadata_column_map,
        source_name="Area metadata",
    )
    area_columns = area_columns.drop_duplicates(subset=["area_code", "area_name"])

    mapped = area_columns.merge(indicator_wide, on=["area_code", "area_name"], how="inner")
    validate_public_health_data(mapped)
    return mapped.loc[:, PUBLIC_HEALTH_REQUIRED_COLUMNS]


__all__ = [
    "AREA_METADATA_COLUMN_ALIASES",
    "DEFAULT_MEDICATION_CLASS_MAP",
    "DEFAULT_OHID_INDICATOR_MAP",
    "OHID_LONG_COLUMN_ALIASES",
    "OPENPRESCRIBING_COLUMN_ALIASES",
    "map_ohid_fingertips_indicator_csv",
    "map_openprescribing_aggregate_csv",
]
