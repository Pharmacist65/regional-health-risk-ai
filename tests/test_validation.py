import pandas as pd
import pytest

from src.validation import (
    collect_prescribing_validation_errors,
    collect_public_health_validation_errors,
    validate_prescribing_data,
    validate_public_health_data,
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
            },
            {
                "month": "2025-01-01",
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "medication_class": "Antihypertensive",
                "items_per_1000": 120.0,
                "cost_per_1000": 300.0,
            },
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


def test_valid_prescribing_data_has_no_errors():
    assert collect_prescribing_validation_errors(valid_prescribing_frame()) == []
    validate_prescribing_data(valid_prescribing_frame())


def test_prescribing_validation_catches_common_failures():
    data = valid_prescribing_frame()
    invalid = pd.concat(
        [data, data.iloc[[0]], data.iloc[[0]], data.iloc[[0]]],
        ignore_index=True,
    )
    invalid["cost_per_1000"] = invalid["cost_per_1000"].astype(object)
    invalid.loc[0, "month"] = "not-a-date"
    invalid.loc[1, "items_per_1000"] = -1
    invalid.loc[1, "cost_per_1000"] = "not-numeric"
    invalid.loc[1, "medication_class"] = "Unsupported"
    invalid.loc[2, "area_code"] = ""

    errors = collect_prescribing_validation_errors(invalid)
    joined = " | ".join(errors)

    assert "month contains values that cannot be parsed as dates" in joined
    assert "items_per_1000 contains negative values" in joined
    assert "cost_per_1000 contains non-numeric values" in joined
    assert "unsupported medication classes" in joined
    assert "area_code contains blank values" in joined
    assert "duplicate rows found for month, area_code and medication_class" in joined


def test_prescribing_validation_raises_clear_message():
    invalid = valid_prescribing_frame().drop(columns=["month"])

    with pytest.raises(ValueError, match="Invalid prescribing data: missing required columns"):
        validate_prescribing_data(invalid)


def test_valid_public_health_data_has_no_errors():
    assert collect_public_health_validation_errors(valid_public_health_frame()) == []
    validate_public_health_data(valid_public_health_frame())


def test_public_health_validation_catches_ranges_and_duplicates():
    invalid = pd.concat([valid_public_health_frame(), valid_public_health_frame()], ignore_index=True)
    invalid.loc[0, "latitude"] = 120
    invalid.loc[0, "obesity_prevalence_pct"] = 140
    invalid.loc[1, "area_name"] = ""

    errors = collect_public_health_validation_errors(invalid)
    joined = " | ".join(errors)

    assert "duplicate rows found for area_code" in joined
    assert "latitude contains values outside -90..90" in joined
    assert "obesity_prevalence_pct contains values outside 0..100" in joined
    assert "area_name contains blank values" in joined


def test_public_health_validation_raises_clear_message():
    invalid = valid_public_health_frame().drop(columns=["area_code"])

    with pytest.raises(ValueError, match="Invalid public health data: missing required columns"):
        validate_public_health_data(invalid)
