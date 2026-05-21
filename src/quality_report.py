"""Data quality reporting helpers for aggregate demo inputs."""

from __future__ import annotations

import pandas as pd

from src.validation import (
    collect_prescribing_validation_errors,
    collect_public_health_validation_errors,
)


QUALITY_REPORT_BOUNDARY = (
    "Synthetic aggregate data quality summary for public-health planning "
    "demonstration only. This is not clinical validation."
)


def _blank_string_count(df: pd.DataFrame) -> int:
    string_columns = df.select_dtypes(include=["object", "string"])
    if string_columns.empty:
        return 0
    return int(
        string_columns.apply(lambda column: column.astype(str).str.strip().eq("").sum()).sum()
    )


def _duplicate_key_rows(df: pd.DataFrame, key_columns: tuple[str, ...]) -> int:
    if not set(key_columns).issubset(df.columns):
        return 0
    return int(df.duplicated(subset=list(key_columns), keep=False).sum())


def build_dataset_quality_summary(
    *,
    dataset: str,
    df: pd.DataFrame,
    validation_errors: list[str],
    key_columns: tuple[str, ...],
) -> dict[str, object]:
    """Summarise one aggregate dataset for dashboard-quality reporting."""
    issue_count = len(validation_errors)
    return {
        "dataset": dataset,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "area_count": int(df["area_code"].nunique()) if "area_code" in df.columns else 0,
        "missing_values": int(df.isna().sum().sum()),
        "blank_values": _blank_string_count(df),
        "duplicate_key_rows": _duplicate_key_rows(df, key_columns),
        "validation_status": "Pass" if issue_count == 0 else "Review required",
        "issue_count": issue_count,
        "issues": "No validation issues detected" if issue_count == 0 else "; ".join(validation_errors),
    }


def build_data_quality_report(
    prescribing_df: pd.DataFrame,
    public_health_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build a compact quality report for the two aggregate input datasets."""
    rows = [
        build_dataset_quality_summary(
            dataset="Aggregate prescribing",
            df=prescribing_df,
            validation_errors=collect_prescribing_validation_errors(prescribing_df),
            key_columns=("month", "area_code", "medication_class"),
        ),
        build_dataset_quality_summary(
            dataset="Public-health indicators",
            df=public_health_df,
            validation_errors=collect_public_health_validation_errors(public_health_df),
            key_columns=("area_code",),
        ),
    ]
    return pd.DataFrame(rows)


def format_data_quality_report_markdown(report_df: pd.DataFrame) -> str:
    """Format a data quality report as non-clinical Markdown."""
    text_df = report_df.astype(str).replace(r"\|", "/", regex=True)
    header = "| " + " | ".join(text_df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(text_df.columns)) + " |"
    rows = [
        "| " + " | ".join(row[column] for column in text_df.columns) + " |"
        for _, row in text_df.iterrows()
    ]
    report_table = "\n".join([header, separator, *rows])
    return "\n".join(
        [
            "# Aggregate Data Quality Report",
            "",
            QUALITY_REPORT_BOUNDARY,
            "",
            report_table,
            "",
            "Interpretation: passing validation means the aggregate demo inputs match the "
            "expected schema and simple quality rules. It does not mean the score is "
            "clinically validated or suitable for individual decision-making.",
        ]
    )
