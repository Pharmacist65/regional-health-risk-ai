from pathlib import Path

import pandas as pd

from src.risk_model import (
    RiskWeights,
    add_planning_signal_profiles,
    build_area_features,
    compute_risk_scores,
    format_area_report_markdown,
    intervention_suggestions,
    prevention_prioritisation_category,
    planning_signal_profile,
    public_health_indicator_snapshot,
    score_component_breakdown,
    summarize_area_prescribing,
    summarize_interventions,
)


ROOT = Path(__file__).resolve().parents[1]


def test_risk_pipeline_runs_on_demo_data():
    prescribing = pd.read_csv(ROOT / "data" / "sample_aggregate_prescribing.csv")
    public_health = pd.read_csv(ROOT / "data" / "sample_public_health_indicators.csv")

    features = build_area_features(prescribing, public_health)
    scored = compute_risk_scores(features)
    interventions = summarize_interventions(scored)

    assert not features.empty
    assert not scored.empty
    assert scored["risk_score"].between(0, 100).all()
    assert {"area_name", "risk_score", "risk_tier"}.issubset(scored.columns)
    assert "suggested_actions" in interventions.columns


def test_planning_signal_profile_uses_largest_weighted_component():
    profile = planning_signal_profile(
        {
            "nsaid_persistence_scaled": 0.2,
            "cardiometabolic_rx_scaled": 1.0,
            "saturated_fat_scaled": 0.1,
            "deprivation_scaled": 0.1,
            "obesity_scaled": 0.1,
        }
    )

    assert profile["primary_planning_signal"] == "Cardiometabolic medicines awareness"
    assert profile["planning_signal_group"] == "Aggregate prescribing signal"
    assert profile["planning_signal_contribution"] == 25.0
    assert "diagnosis" not in profile["planning_signal_detail"].lower()


def test_planning_signal_profile_returns_routine_monitoring_for_zero_signal():
    profile = planning_signal_profile(
        {
            "nsaid_persistence_scaled": 0,
            "cardiometabolic_rx_scaled": 0,
            "saturated_fat_scaled": 0,
            "deprivation_scaled": 0,
            "obesity_scaled": 0,
        }
    )

    assert profile["primary_planning_signal"] == "Routine aggregate monitoring"
    assert profile["planning_signal_contribution"] == 0.0


def test_add_planning_signal_profiles_adds_dashboard_explanation_columns():
    scored = pd.DataFrame(
        [
            {
                "area_code": "A001",
                "area_name": "Demo Area",
                "risk_score": 25,
                "risk_tier": "Moderate",
                "nsaid_persistence_scaled": 1.0,
                "cardiometabolic_rx_scaled": 0,
                "saturated_fat_scaled": 0,
                "deprivation_scaled": 0,
                "obesity_scaled": 0,
            }
        ]
    )

    output = add_planning_signal_profiles(scored)

    assert output.loc[0, "primary_planning_signal"] == "NSAID safety awareness"
    assert output.loc[0, "planning_signal_group"] == "Aggregate prescribing signal"
    assert output.loc[0, "planning_signal_contribution"] == 35.0


def test_public_health_indicator_snapshot_is_sorted_and_non_clinical():
    snapshot = public_health_indicator_snapshot(
        {
            "saturated_fat_proxy_index": 50,
            "deprivation_index": 70,
            "obesity_prevalence_pct": 30,
            "hypertension_prevalence_estimate_pct": 20,
            "diabetes_prevalence_estimate_pct": 8,
        }
    )

    assert list(snapshot.columns) == [
        "indicator",
        "synthetic_aggregate_value",
        "safe_interpretation",
    ]
    assert snapshot["synthetic_aggregate_value"].is_monotonic_decreasing
    assert snapshot.iloc[0]["indicator"] == "Deprivation index"
    assert set(snapshot["safe_interpretation"]) == {"Aggregate planning context only"}


def test_score_component_breakdown_explains_score_contributions():
    prescribing = pd.read_csv(ROOT / "data" / "sample_aggregate_prescribing.csv")
    public_health = pd.read_csv(ROOT / "data" / "sample_public_health_indicators.csv")
    scored = compute_risk_scores(build_area_features(prescribing, public_health))

    row = scored.iloc[0]
    breakdown = score_component_breakdown(row)

    assert list(breakdown.columns) == [
        "component",
        "input_value",
        "scaled_signal",
        "weight_pct",
        "score_contribution",
        "interpretation",
    ]
    assert len(breakdown) == 5
    assert breakdown["weight_pct"].sum() == 100
    assert abs(breakdown["score_contribution"].sum() - row["risk_score"]) <= 0.3


def test_area_report_preserves_public_health_boundary():
    row = {
        "area_name": "Demo Area",
        "area_code": "DEMO001",
        "risk_score": 72.5,
        "risk_tier": "High",
        "nsaid_mean_items_per_1000": 104.2,
        "cardiometabolic_rx_density": 315.4,
        "deprivation_index": 62.1,
        "obesity_prevalence_pct": 29.4,
    }

    prescribing_indicators = pd.DataFrame(
        [
            {
                "medication_class": "NSAID",
                "mean_items_per_1000": 104.2,
                "max_items_per_1000": 121.7,
                "mean_cost_per_1000": 305.33,
            }
        ]
    )
    public_health_indicators = {
        "saturated_fat_proxy_index": 61.4,
        "deprivation_index": 62.1,
        "obesity_prevalence_pct": 29.4,
        "hypertension_prevalence_estimate_pct": 17.2,
        "diabetes_prevalence_estimate_pct": 7.6,
    }

    report = format_area_report_markdown(
        row,
        ["Use aggregate pharmacy awareness materials."],
        prescribing_indicators=prescribing_indicators,
        public_health_indicators=public_health_indicators,
    )

    assert "synthetic aggregate data only" in report
    assert "Not affiliated with the NHS" in report
    assert "Not medical advice" in report
    assert "No patient-level data" in report
    assert "Aggregate prescribing indicators" in report
    assert "Public health indicators" in report
    assert "Prevention-prioritisation category: High prevention-prioritisation signal" in report
    assert "| NSAID | 104.2 | 121.7 | 305.33 |" in report
    assert "| Hypertension prevalence estimate (%) | 17.2 |" in report
    assert "Use aggregate pharmacy awareness materials." in report


def test_summarize_area_prescribing_returns_aggregate_indicators():
    prescribing = pd.read_csv(ROOT / "data" / "sample_aggregate_prescribing.csv")
    camden_prescribing = prescribing[prescribing["area_name"] == "Camden"]

    summary = summarize_area_prescribing(camden_prescribing)

    assert set(summary.columns) == {
        "medication_class",
        "mean_items_per_1000",
        "max_items_per_1000",
        "mean_cost_per_1000",
    }
    assert set(summary["medication_class"]) == {
        "NSAID",
        "Antihypertensive",
        "Lipid-lowering",
        "Antidiabetic",
    }
    assert summary["mean_items_per_1000"].is_monotonic_decreasing


def test_prevention_prioritisation_category_is_non_clinical():
    assert prevention_prioritisation_category({"risk_tier": "Low"}) == "Routine aggregate monitoring"
    assert (
        prevention_prioritisation_category({"risk_tier": "Very high"})
        == "Very high prevention-prioritisation signal"
    )
    assert prevention_prioritisation_category({"risk_tier": "Unknown"}) == "Uncategorised planning signal"


def test_intervention_suggestions_remain_non_clinical():
    suggestions = intervention_suggestions(
        {
            "nsaid_persistence_scaled": 1,
            "cardiometabolic_rx_scaled": 1,
            "saturated_fat_scaled": 1,
            "obesity_scaled": 1,
            "deprivation_scaled": 1,
        }
    )

    joined = " ".join(suggestions).lower()
    unsafe_terms = ["diagnose", "dose", "prescribe", "supplement"]
    assert suggestions
    assert all(term not in joined for term in unsafe_terms)


def test_summarize_interventions_preserves_planning_signal_columns():
    scored = pd.DataFrame(
        [
            {
                "area_code": "A001",
                "area_name": "Demo Area",
                "risk_score": 25,
                "risk_tier": "Moderate",
                "primary_planning_signal": "NSAID safety awareness",
                "planning_signal_group": "Aggregate prescribing signal",
            }
        ]
    )

    summary = summarize_interventions(scored)

    assert "primary_planning_signal" in summary.columns
    assert "planning_signal_group" in summary.columns


def test_risk_weights_must_sum_to_positive_value():
    features = pd.DataFrame(
        [
            {
                "nsaid_mean_items_per_1000": 10,
                "cardiometabolic_rx_density": 20,
                "saturated_fat_proxy_index": 30,
                "deprivation_index": 40,
                "obesity_prevalence_pct": 50,
            }
        ]
    )

    zero_weights = RiskWeights(
        nsaid_persistence=0,
        cardiometabolic_rx_density=0,
        saturated_fat_proxy=0,
        deprivation=0,
        obesity=0,
    )

    try:
        compute_risk_scores(features, weights=zero_weights)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("Expected zero-sum weights to raise ValueError")
