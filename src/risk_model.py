"""Risk scoring utilities for the Regional Health Risk Optimisation MVP.

This module is intentionally designed for portfolio and proof-of-concept use.
It does not provide clinical advice, diagnosis, or treatment recommendations.
It operates on anonymised, aggregated area-level indicators only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


MEDICATION_CLASSES = [
    "NSAID",
    "Antihypertensive",
    "Lipid-lowering",
    "Antidiabetic",
]


@dataclass(frozen=True)
class RiskWeights:
    """Weights used for the demonstration composite score.

    The values are illustrative and should be replaced with validated weights
    before any real-world use.
    """

    nsaid_persistence: float = 0.35
    cardiometabolic_rx_density: float = 0.25
    saturated_fat_proxy: float = 0.20
    deprivation: float = 0.10
    obesity: float = 0.10


DEFAULT_WEIGHTS = RiskWeights()


SCORE_COMPONENTS = [
    {
        "label": "NSAID persistence signal",
        "raw_column": "nsaid_mean_items_per_1000",
        "scaled_column": "nsaid_persistence_scaled",
        "weight_attr": "nsaid_persistence",
        "interpretation": "Area-level NSAID item volume averaged across the synthetic demo year.",
    },
    {
        "label": "Cardiometabolic prescribing density",
        "raw_column": "cardiometabolic_rx_density",
        "scaled_column": "cardiometabolic_rx_scaled",
        "weight_attr": "cardiometabolic_rx_density",
        "interpretation": "Combined aggregate antihypertensive, lipid-lowering and antidiabetic item density.",
    },
    {
        "label": "Saturated-fat proxy",
        "raw_column": "saturated_fat_proxy_index",
        "scaled_column": "saturated_fat_scaled",
        "weight_attr": "saturated_fat_proxy",
        "interpretation": "Synthetic area-level public-health proxy, included to demonstrate contextual risk factors.",
    },
    {
        "label": "Deprivation index",
        "raw_column": "deprivation_index",
        "scaled_column": "deprivation_scaled",
        "weight_attr": "deprivation",
        "interpretation": "Synthetic area-level deprivation proxy for prevention access and communication planning.",
    },
    {
        "label": "Obesity prevalence estimate",
        "raw_column": "obesity_prevalence_pct",
        "scaled_column": "obesity_scaled",
        "weight_attr": "obesity",
        "interpretation": "Synthetic aggregate prevalence estimate used only for population-level prioritisation.",
    },
]

PUBLIC_HEALTH_REPORT_FIELDS = [
    ("saturated_fat_proxy_index", "Saturated-fat proxy index"),
    ("deprivation_index", "Deprivation index"),
    ("obesity_prevalence_pct", "Obesity prevalence estimate (%)"),
    ("hypertension_prevalence_estimate_pct", "Hypertension prevalence estimate (%)"),
    ("diabetes_prevalence_estimate_pct", "Diabetes prevalence estimate (%)"),
]


PRIORITISATION_CATEGORY_BY_TIER = {
    "Low": "Routine aggregate monitoring",
    "Moderate": "Moderate prevention-prioritisation signal",
    "High": "High prevention-prioritisation signal",
    "Very high": "Very high prevention-prioritisation signal",
}


def _weight_total(weights: RiskWeights) -> float:
    total_weight = sum(weights.__dict__.values())
    if total_weight <= 0:
        raise ValueError("Risk weights must sum to a positive value.")
    return total_weight


def _minmax(series: pd.Series) -> pd.Series:
    """Scale a numeric series to 0..1 while handling constant columns."""
    values = pd.to_numeric(series, errors="coerce").astype(float)
    min_value = values.min()
    max_value = values.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - min_value) / (max_value - min_value)


def validate_prescribing_frame(df: pd.DataFrame) -> None:
    required = {
        "month",
        "area_code",
        "area_name",
        "medication_class",
        "items_per_1000",
        "cost_per_1000",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Prescribing data is missing required columns: {sorted(missing)}")


def validate_public_health_frame(df: pd.DataFrame) -> None:
    required = {
        "area_code",
        "area_name",
        "saturated_fat_proxy_index",
        "deprivation_index",
        "obesity_prevalence_pct",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Public health data is missing required columns: {sorted(missing)}")


def build_area_features(
    prescribing_df: pd.DataFrame,
    public_health_df: pd.DataFrame,
) -> pd.DataFrame:
    """Create area-level modelling features from aggregate prescribing data.

    Parameters
    ----------
    prescribing_df:
        Monthly area-level prescribing indicators. Each row is an aggregate
        medication-class observation, not a patient record.
    public_health_df:
        Area-level public health indicators.

    Returns
    -------
    pandas.DataFrame
        One row per area with derived features.
    """
    validate_prescribing_frame(prescribing_df)
    validate_public_health_frame(public_health_df)

    df = prescribing_df.copy()
    df["month"] = pd.to_datetime(df["month"])
    df["items_per_1000"] = pd.to_numeric(df["items_per_1000"], errors="coerce")
    df["cost_per_1000"] = pd.to_numeric(df["cost_per_1000"], errors="coerce")

    class_means = (
        df.groupby(["area_code", "area_name", "medication_class"], as_index=False)
        .agg(
            mean_items_per_1000=("items_per_1000", "mean"),
            max_items_per_1000=("items_per_1000", "max"),
            mean_cost_per_1000=("cost_per_1000", "mean"),
        )
    )

    pivot = class_means.pivot_table(
        index=["area_code", "area_name"],
        columns="medication_class",
        values="mean_items_per_1000",
        fill_value=0,
    ).reset_index()
    pivot.columns.name = None

    for med_class in MEDICATION_CLASSES:
        if med_class not in pivot.columns:
            pivot[med_class] = 0.0

    nsaid = df[df["medication_class"] == "NSAID"].copy()
    nsaid_persistence = (
        nsaid.groupby(["area_code", "area_name"], as_index=False)
        .agg(
            nsaid_mean_items_per_1000=("items_per_1000", "mean"),
            nsaid_months_above_area_median=(
                "items_per_1000",
                lambda s: int((s > s.median()).sum()),
            ),
        )
    )

    features = pivot.merge(nsaid_persistence, on=["area_code", "area_name"], how="left")
    features["nsaid_mean_items_per_1000"] = features["nsaid_mean_items_per_1000"].fillna(0)
    features["nsaid_months_above_area_median"] = features["nsaid_months_above_area_median"].fillna(0)

    features["cardiometabolic_rx_density"] = (
        features["Antihypertensive"]
        + features["Lipid-lowering"]
        + features["Antidiabetic"]
    )

    return features.merge(public_health_df, on=["area_code", "area_name"], how="left")


def compute_risk_scores(
    features_df: pd.DataFrame,
    weights: RiskWeights = DEFAULT_WEIGHTS,
) -> pd.DataFrame:
    """Compute an illustrative regional risk score.

    The score is a portfolio demonstration, not a validated clinical score.
    """
    df = features_df.copy()

    required = [
        "nsaid_mean_items_per_1000",
        "cardiometabolic_rx_density",
        "saturated_fat_proxy_index",
        "deprivation_index",
        "obesity_prevalence_pct",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Feature data is missing required columns: {missing}")

    df["nsaid_persistence_scaled"] = _minmax(df["nsaid_mean_items_per_1000"])
    df["cardiometabolic_rx_scaled"] = _minmax(df["cardiometabolic_rx_density"])
    df["saturated_fat_scaled"] = _minmax(df["saturated_fat_proxy_index"])
    df["deprivation_scaled"] = _minmax(df["deprivation_index"])
    df["obesity_scaled"] = _minmax(df["obesity_prevalence_pct"])

    total_weight = _weight_total(weights)
    raw_score = (
        weights.nsaid_persistence * df["nsaid_persistence_scaled"]
        + weights.cardiometabolic_rx_density * df["cardiometabolic_rx_scaled"]
        + weights.saturated_fat_proxy * df["saturated_fat_scaled"]
        + weights.deprivation * df["deprivation_scaled"]
        + weights.obesity * df["obesity_scaled"]
    ) / total_weight

    df["risk_score"] = (raw_score * 100).round(1)
    df["risk_tier"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Low", "Moderate", "High", "Very high"],
    ).astype(str)

    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def intervention_suggestions(row: pd.Series | dict) -> list[str]:
    """Return non-clinical, guideline-aligned intervention suggestions.

    These suggestions are intentionally framed as awareness and workflow actions.
    They are not patient-level medical recommendations.
    """
    data = dict(row)
    suggestions: list[str] = []

    if data.get("nsaid_persistence_scaled", 0) >= 0.6:
        suggestions.append(
            "Prioritise NSAID safety awareness materials through community pharmacies."
        )
    if data.get("cardiometabolic_rx_scaled", 0) >= 0.6:
        suggestions.append(
            "Prepare GP/pharmacy briefing on adherence and interaction awareness for cardiometabolic medicines."
        )
    if data.get("saturated_fat_scaled", 0) >= 0.6 or data.get("obesity_scaled", 0) >= 0.6:
        suggestions.append(
            "Deploy guideline-aligned lifestyle risk awareness content; avoid individual dietary advice."
        )
    if data.get("deprivation_scaled", 0) >= 0.6:
        suggestions.append(
            "Use plain-language materials and pharmacy-led signposting to local support services."
        )

    if not suggestions:
        suggestions.append(
            "Maintain routine monitoring and update the area profile when new aggregate data becomes available."
        )
    return suggestions


def prevention_prioritisation_category(row: pd.Series | dict) -> str:
    """Return a non-clinical planning category for a scored area."""
    data = dict(row)
    risk_tier = str(data.get("risk_tier", "Unknown"))
    return PRIORITISATION_CATEGORY_BY_TIER.get(risk_tier, "Uncategorised planning signal")


def summarize_area_prescribing(prescribing_df: pd.DataFrame) -> pd.DataFrame:
    """Summarise selected-region aggregate prescribing indicators by class."""
    validate_prescribing_frame(prescribing_df)
    summary = (
        prescribing_df.copy()
        .assign(
            items_per_1000=lambda df: pd.to_numeric(df["items_per_1000"], errors="coerce"),
            cost_per_1000=lambda df: pd.to_numeric(df["cost_per_1000"], errors="coerce"),
        )
        .groupby("medication_class", as_index=False)
        .agg(
            mean_items_per_1000=("items_per_1000", "mean"),
            max_items_per_1000=("items_per_1000", "max"),
            mean_cost_per_1000=("cost_per_1000", "mean"),
        )
        .sort_values("mean_items_per_1000", ascending=False)
    )
    summary["mean_items_per_1000"] = summary["mean_items_per_1000"].round(1)
    summary["max_items_per_1000"] = summary["max_items_per_1000"].round(1)
    summary["mean_cost_per_1000"] = summary["mean_cost_per_1000"].round(2)
    return summary.reset_index(drop=True)


def score_component_breakdown(
    row: pd.Series | dict,
    weights: RiskWeights = DEFAULT_WEIGHTS,
) -> pd.DataFrame:
    """Return an interpretable contribution table for one scored area."""
    data = dict(row)
    total_weight = _weight_total(weights)
    rows = []

    for component in SCORE_COMPONENTS:
        raw_value = pd.to_numeric(
            pd.Series([data.get(component["raw_column"], 0)]), errors="coerce"
        ).iloc[0]
        scaled_value = pd.to_numeric(
            pd.Series([data.get(component["scaled_column"], 0)]), errors="coerce"
        ).iloc[0]

        if pd.isna(raw_value):
            raw_value = 0.0
        if pd.isna(scaled_value):
            scaled_value = 0.0

        weight = getattr(weights, component["weight_attr"])
        rows.append(
            {
                "component": component["label"],
                "input_value": round(float(raw_value), 2),
                "scaled_signal": round(float(scaled_value), 3),
                "weight_pct": round((weight / total_weight) * 100, 1),
                "score_contribution": round((float(scaled_value) * weight / total_weight) * 100, 1),
                "interpretation": component["interpretation"],
            }
        )

    return pd.DataFrame(rows)


def format_area_report_markdown(
    row: pd.Series | dict,
    suggested_actions: Iterable[str] | str,
    prescribing_indicators: pd.DataFrame | None = None,
    public_health_indicators: pd.Series | dict | None = None,
) -> str:
    """Create a non-clinical regional planning report for download."""
    data = dict(row)
    if isinstance(suggested_actions, str):
        actions = [action.strip() for action in suggested_actions.split("|") if action.strip()]
    else:
        actions = [str(action).strip() for action in suggested_actions if str(action).strip()]

    if not actions:
        actions = ["Maintain aggregate monitoring and refresh the area profile when new data is available."]
    action_lines = "\n".join(f"- {action}" for action in actions)

    if prescribing_indicators is None:
        prescribing_indicators = pd.DataFrame(
            [
                {
                    "medication_class": "NSAID",
                    "mean_items_per_1000": data.get("nsaid_mean_items_per_1000", 0),
                    "max_items_per_1000": data.get("nsaid_mean_items_per_1000", 0),
                    "mean_cost_per_1000": 0,
                },
                {
                    "medication_class": "Cardiometabolic medicines",
                    "mean_items_per_1000": data.get("cardiometabolic_rx_density", 0),
                    "max_items_per_1000": data.get("cardiometabolic_rx_density", 0),
                    "mean_cost_per_1000": 0,
                },
            ]
        )

    public_health_data = dict(public_health_indicators) if public_health_indicators is not None else data
    prescribing_lines = [
        "| Medication class | Mean items per 1,000 | Max items per 1,000 | Mean cost per 1,000 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in prescribing_indicators.to_dict("records"):
        prescribing_lines.append(
            "| {medication_class} | {mean_items_per_1000:.1f} | {max_items_per_1000:.1f} | {mean_cost_per_1000:.2f} |".format(
                medication_class=item.get("medication_class", "Unknown"),
                mean_items_per_1000=float(item.get("mean_items_per_1000", 0)),
                max_items_per_1000=float(item.get("max_items_per_1000", 0)),
                mean_cost_per_1000=float(item.get("mean_cost_per_1000", 0)),
            )
        )

    public_health_lines = [
        "| Indicator | Synthetic aggregate value |",
        "| --- | ---: |",
    ]
    for key, label in PUBLIC_HEALTH_REPORT_FIELDS:
        if key in public_health_data and pd.notna(public_health_data[key]):
            public_health_lines.append(f"| {label} | {float(public_health_data[key]):.1f} |")

    area_name = data.get("area_name", "Selected area")
    area_code = data.get("area_code", "unknown")
    risk_score = float(data.get("risk_score", 0))
    risk_tier = data.get("risk_tier", "Unknown")
    prioritisation_category = prevention_prioritisation_category(data)

    return f"""# Regional public-health planning report: {area_name}

> Portfolio demonstration using synthetic aggregate data only. Not affiliated with the NHS. Not medical advice. No patient-level data.

## Safe-use boundary

This report is for aggregate public-health planning and portfolio demonstration only. It must not be used for individual clinical decisions, medication changes or personalised recommendations.

## Region snapshot

- Area code: {area_code}
- Composite demo risk score: {risk_score:.1f}
- Demo risk tier: {risk_tier}
- Prevention-prioritisation category: {prioritisation_category}

## Aggregate prescribing indicators

{chr(10).join(prescribing_lines)}

## Public health indicators

{chr(10).join(public_health_lines)}

## Suggested awareness/intervention categories

{action_lines}

## Interpretation note

The score is an illustrative composite of scaled aggregate indicators. It is not clinically validated and should be read as a transparent demo of prevention-prioritisation analytics.
"""


def summarize_interventions(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Create an area-level intervention summary table."""
    output = scored_df.copy()
    output["suggested_actions"] = output.apply(
        lambda row: " | ".join(intervention_suggestions(row)), axis=1
    )
    return output[
        [
            "area_code",
            "area_name",
            "risk_score",
            "risk_tier",
            "suggested_actions",
        ]
    ]
