import pandas as pd
import pytest

from src.connectors import (
    OHID_FINGERTIPS_INDICATOR_COLUMNS,
    OPENPRESCRIBING_AGGREGATE_COLUMNS,
    load_ohid_fingertips_public_health_indicators,
    load_openprescribing_aggregate_prescribing,
)


def test_openprescribing_stub_returns_synthetic_aggregate_data():
    result = load_openprescribing_aggregate_prescribing()

    assert result.name == "openprescribing_aggregate_prescribing_stub"
    assert result.is_live_call is False
    assert result.expected_columns == OPENPRESCRIBING_AGGREGATE_COLUMNS
    assert set(OPENPRESCRIBING_AGGREGATE_COLUMNS).issubset(result.data.columns)
    assert not result.data.empty
    assert "No API keys" in result.notes
    assert "patient-level" in result.notes


def test_ohid_fingertips_stub_returns_synthetic_public_health_data():
    result = load_ohid_fingertips_public_health_indicators()

    assert result.name == "ohid_fingertips_public_health_stub"
    assert result.is_live_call is False
    assert result.expected_columns == OHID_FINGERTIPS_INDICATOR_COLUMNS
    assert set(OHID_FINGERTIPS_INDICATOR_COLUMNS).issubset(result.data.columns)
    assert not result.data.empty
    assert "No API keys" in result.notes
    assert "patient-level" in result.notes


def test_connector_stubs_allow_local_csv_overrides(tmp_path):
    prescribing_path = tmp_path / "prescribing.csv"
    prescribing_data = pd.DataFrame(
        [
            {
                "month": "2025-01-01",
                "area_code": "DEMO001",
                "area_name": "Demo Area",
                "medication_class": "NSAID",
                "items_per_1000": 10.5,
                "cost_per_1000": 22.1,
            }
        ]
    )
    prescribing_data.to_csv(prescribing_path, index=False)

    result = load_openprescribing_aggregate_prescribing(prescribing_path)

    assert result.source == str(prescribing_path)
    assert result.data.to_dict("records") == prescribing_data.to_dict("records")


def test_connector_stubs_do_not_make_live_calls():
    with pytest.raises(NotImplementedError, match="Live OpenPrescribing API access"):
        load_openprescribing_aggregate_prescribing(use_live_api=True)

    with pytest.raises(NotImplementedError, match="Live OHID/Fingertips API access"):
        load_ohid_fingertips_public_health_indicators(use_live_api=True)


def test_connector_validation_rejects_missing_columns(tmp_path):
    invalid_path = tmp_path / "invalid.csv"
    pd.DataFrame([{"area_code": "DEMO001"}]).to_csv(invalid_path, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        load_openprescribing_aggregate_prescribing(invalid_path)
