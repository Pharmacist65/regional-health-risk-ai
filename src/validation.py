"""Validation helpers for aggregate health analytics inputs.

The checks in this module are intentionally simple and transparent. They are
designed to catch common data-quality issues before the dashboard or scoring
pipeline runs, while preserving the project's public-health boundary: aggregate
area-level data only, no patient records.
"""

from __future__ import annotations

import pandas as pd


SUPPORTED_MEDICATION_CLASSES = {
    "NSAID",
    "Antihypertensive",
    "Lipid-lowering",
    "Antidiabetic",
}

PRESCRIBING_REQUIRED_COLUMNS = (
    "month",
    "area_code",
    "area_name",
    "medication_class",
    "items_per_1000",
    "cost_per_1000",
)

PUBLIC_HEALTH_REQUIRED_COLUMNS = (
    "area_code",
    "area_name",
    "latitude",
    "longitude",
    "saturated_fat_proxy_index",
    "deprivation_index",
    "obesity_prevalence_pct",
    "hypertension_prevalence_estimate_pct",
    "diabetes_prevalence_estimate_pct",
)

PUBLIC_HEALTH_RANGES = {
    "latitude": (-90, 90),
    "longitude": (-180, 180),
    "saturated_fat_proxy_index": (0, 100),
    "deprivation_index": (0, 100),
    "obesity_prevalence_pct": (0, 100),
    "hypertension_prevalence_estimate_pct": (0, 100),
    "diabetes_prevalence_estimate_pct": (0, 100),
}


def _missing_required_columns(df: pd.DataFrame, required_columns: tuple[str, ...]) -> list[str]:
    missing = sorted(set(required_columns) - set(df.columns))
    if not missing:
        return []
    return [f"missing required columns: {missing}"]


def _blank_values(df: pd.DataFrame, columns: tuple[str, ...]) -> list[str]:
    errors = []
    for column in columns:
        if column in df.columns and df[column].isna().any():
            errors.append(f"{column} contains missing values")
        if column in df.columns and df[column].astype(str).str.strip().eq("").any():
            errors.append(f"{column} contains blank values")
    return errors


def collect_prescribing_validation_errors(df: pd.DataFrame) -> list[str]:
    """Return validation errors for aggregate prescribing input data."""
    errors = _missing_required_columns(df, PRESCRIBING_REQUIRED_COLUMNS)
    if errors:
        return errors

    errors.extend(_blank_values(df, ("area_code", "area_name", "medication_class")))

    parsed_months = pd.to_datetime(df["month"], errors="coerce", format="%Y-%m-%d")
    if parsed_months.isna().any():
        errors.append("month contains values that cannot be parsed as dates")

    duplicate_mask = df.duplicated(
        subset=["month", "area_code", "medication_class"],
        keep=False,
    )
    if duplicate_mask.any():
        errors.append("duplicate rows found for month, area_code and medication_class")

    unknown_medication_classes = sorted(
        set(df["medication_class"].dropna().astype(str)) - SUPPORTED_MEDICATION_CLASSES
    )
    if unknown_medication_classes:
        errors.append(f"unsupported medication classes: {unknown_medication_classes}")

    for column in ("items_per_1000", "cost_per_1000"):
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any():
            errors.append(f"{column} contains non-numeric values")
        if (numeric < 0).any():
            errors.append(f"{column} contains negative values")

    return errors


def validate_prescribing_data(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if aggregate prescribing input data is invalid."""
    errors = collect_prescribing_validation_errors(df)
    if errors:
        raise ValueError("Invalid prescribing data: " + "; ".join(errors))


def collect_public_health_validation_errors(df: pd.DataFrame) -> list[str]:
    """Return validation errors for aggregate public-health indicator data."""
    errors = _missing_required_columns(df, PUBLIC_HEALTH_REQUIRED_COLUMNS)
    if errors:
        return errors

    errors.extend(_blank_values(df, ("area_code", "area_name")))

    duplicate_mask = df.duplicated(subset=["area_code"], keep=False)
    if duplicate_mask.any():
        errors.append("duplicate rows found for area_code")

    for column, (minimum, maximum) in PUBLIC_HEALTH_RANGES.items():
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any():
            errors.append(f"{column} contains non-numeric values")
            continue
        if ((numeric < minimum) | (numeric > maximum)).any():
            errors.append(f"{column} contains values outside {minimum}..{maximum}")

    return errors


def validate_public_health_data(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if aggregate public-health indicator data is invalid."""
    errors = collect_public_health_validation_errors(df)
    if errors:
        raise ValueError("Invalid public health data: " + "; ".join(errors))
