import pandas as pd

from src.quality_report import (
    QUALITY_REPORT_BOUNDARY,
    build_data_quality_report,
    format_data_quality_report_markdown,
)


def valid_prescribing_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "month": "2025-01-01",
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "medication_class": "NSAID",
                "items_per_1000": 100.0,
                "cost_per_1000": 250.0,
            }
        ]
    )


def valid_public_health_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "latitude": 51.5,
                "longitude": -0.1,
                "saturated_fat_proxy_index": 62.0,
                "deprivation_index": 48.0,
                "obesity_prevalence_pct": 28.0,
                "hypertension_prevalence_estimate_pct": 18.0,
                "diabetes_prevalence_estimate_pct": 7.0,
            }
        ]
    )


def test_data_quality_report_passes_for_valid_aggregate_frames():
    report = build_data_quality_report(valid_prescribing_frame(), valid_public_health_frame())

    assert report["dataset"].tolist() == [
        "Aggregate prescribing",
        "Public-health indicators",
    ]
    assert report["validation_status"].tolist() == ["Pass", "Pass"]
    assert report["issue_count"].tolist() == [0, 0]
    assert report["area_count"].tolist() == [1, 1]


def test_data_quality_report_flags_invalid_aggregate_frames():
    prescribing = valid_prescribing_frame().drop(columns=["month"])
    public_health = valid_public_health_frame()
    public_health.loc[0, "obesity_prevalence_pct"] = 180

    report = build_data_quality_report(prescribing, public_health)

    assert report["validation_status"].tolist() == ["Review required", "Review required"]
    assert report["issue_count"].min() > 0
    assert "missing required columns" in report.loc[0, "issues"]
    assert "obesity_prevalence_pct contains values outside 0..100" in report.loc[1, "issues"]


def test_quality_report_markdown_keeps_non_clinical_boundary():
    report = build_data_quality_report(valid_prescribing_frame(), valid_public_health_frame())

    markdown = format_data_quality_report_markdown(report)

    assert "# Aggregate Data Quality Report" in markdown
    assert QUALITY_REPORT_BOUNDARY in markdown
    assert "not clinical validation" in markdown
    assert "Aggregate prescribing" in markdown
