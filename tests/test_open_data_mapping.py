import pandas as pd
import pytest

from src.open_data_mapping import (
    map_ohid_fingertips_indicator_csv,
    map_openprescribing_aggregate_csv,
)


def test_maps_openprescribing_style_csv_to_prescribing_schema(tmp_path):
    source_path = tmp_path / "openprescribing_extract.csv"
    pd.DataFrame(
        [
            {
                "period": "2025-01",
                "org_code": "AREA001",
                "org_name": "Demo Area",
                "measure_name": "Non-steroidal anti-inflammatory drugs",
                "items_per_1000_patients": 8.5,
                "actual_cost_per_1000": 18.0,
            },
            {
                "period": "2025-01",
                "org_code": "AREA001",
                "org_name": "Demo Area",
                "measure_name": "NSAID",
                "items_per_1000_patients": 1.5,
                "actual_cost_per_1000": 4.0,
            },
            {
                "period": "2025-01",
                "org_code": "AREA001",
                "org_name": "Demo Area",
                "measure_name": "Antihypertensives",
                "items_per_1000_patients": 12.0,
                "actual_cost_per_1000": 22.0,
            },
        ]
    ).to_csv(source_path, index=False)

    mapped = map_openprescribing_aggregate_csv(source_path)

    assert list(mapped.columns) == [
        "month",
        "area_code",
        "area_name",
        "medication_class",
        "items_per_1000",
        "cost_per_1000",
    ]
    assert mapped["month"].tolist() == ["2025-01-01", "2025-01-01"]
    nsaid_row = mapped[mapped["medication_class"] == "NSAID"].iloc[0]
    assert nsaid_row["items_per_1000"] == 10.0
    assert nsaid_row["cost_per_1000"] == 22.0


def test_openprescribing_mapping_accepts_explicit_column_and_class_maps(tmp_path):
    source_path = tmp_path / "custom_extract.csv"
    pd.DataFrame(
        [
            {
                "month_label": "2025-02-01",
                "local_code": "AREA002",
                "local_name": "Example Area",
                "class_label": "bp medicines",
                "item_rate": 30,
                "cost_rate": 50,
            }
        ]
    ).to_csv(source_path, index=False)

    mapped = map_openprescribing_aggregate_csv(
        source_path,
        column_map={
            "month": "month_label",
            "area_code": "local_code",
            "area_name": "local_name",
            "medication_class": "class_label",
            "items_per_1000": "item_rate",
            "cost_per_1000": "cost_rate",
        },
        medication_class_map={"bp medicines": "Antihypertensive"},
    )

    assert mapped.to_dict("records") == [
        {
            "month": "2025-02-01",
            "area_code": "AREA002",
            "area_name": "Example Area",
            "medication_class": "Antihypertensive",
            "items_per_1000": 30,
            "cost_per_1000": 50,
        }
    ]


def test_openprescribing_mapping_rejects_missing_source_columns(tmp_path):
    source_path = tmp_path / "invalid_openprescribing.csv"
    pd.DataFrame([{"org_code": "AREA001"}]).to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="missing required source columns"):
        map_openprescribing_aggregate_csv(source_path)


def test_openprescribing_mapping_rejects_unsupported_medication_class(tmp_path):
    source_path = tmp_path / "unsupported_class.csv"
    pd.DataFrame(
        [
            {
                "month": "2025-01-01",
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "medication_class": "Unmapped medication group",
                "items_per_1000": 10,
                "cost_per_1000": 20,
            }
        ]
    ).to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="unsupported medication classes"):
        map_openprescribing_aggregate_csv(source_path)


def test_openprescribing_mapping_rejects_non_numeric_rates(tmp_path):
    source_path = tmp_path / "non_numeric_rates.csv"
    pd.DataFrame(
        [
            {
                "month": "2025-01-01",
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "medication_class": "NSAID",
                "items_per_1000": "not numeric",
                "cost_per_1000": 20,
            }
        ]
    ).to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="items_per_1000 contains non-numeric values"):
        map_openprescribing_aggregate_csv(source_path)


def test_maps_ohid_fingertips_long_csv_to_public_health_schema(tmp_path):
    source_path = tmp_path / "fingertips_extract.csv"
    rows = []
    for indicator_name, value in [
        ("Saturated fat proxy index", 62.0),
        ("Deprivation index", 45.0),
        ("Obesity prevalence", 28.5),
        ("Hypertension prevalence estimate", 18.1),
        ("Diabetes prevalence estimate", 7.2),
    ]:
        rows.append(
            {
                "Area Code": "AREA001",
                "Area Name": "Demo Area",
                "Indicator Name": indicator_name,
                "Value": value,
                "Latitude": 51.5,
                "Longitude": -0.1,
            }
        )
    pd.DataFrame(rows).to_csv(source_path, index=False)

    mapped = map_ohid_fingertips_indicator_csv(source_path)

    assert mapped.to_dict("records") == [
        {
            "area_code": "AREA001",
            "area_name": "Demo Area",
            "latitude": 51.5,
            "longitude": -0.1,
            "saturated_fat_proxy_index": 62.0,
            "deprivation_index": 45.0,
            "obesity_prevalence_pct": 28.5,
            "hypertension_prevalence_estimate_pct": 18.1,
            "diabetes_prevalence_estimate_pct": 7.2,
        }
    ]


def test_ohid_mapping_accepts_separate_area_metadata(tmp_path):
    indicator_path = tmp_path / "indicator_extract.csv"
    metadata_path = tmp_path / "area_metadata.csv"
    pd.DataFrame(
        [
            {"area_code": "AREA001", "area_name": "Demo Area", "indicator_name": name, "value": value}
            for name, value in [
                ("Saturated fat proxy index", 62.0),
                ("Deprivation index", 45.0),
                ("Obesity prevalence", 28.5),
                ("Hypertension prevalence estimate", 18.1),
                ("Diabetes prevalence estimate", 7.2),
            ]
        ]
    ).to_csv(indicator_path, index=False)
    pd.DataFrame(
        [
            {
                "area_code": "AREA001",
                "area_name": "Demo Area",
                "latitude": 51.5,
                "longitude": -0.1,
            }
        ]
    ).to_csv(metadata_path, index=False)

    mapped = map_ohid_fingertips_indicator_csv(
        indicator_path,
        area_metadata=metadata_path,
    )

    assert mapped.loc[0, "latitude"] == 51.5
    assert mapped.loc[0, "longitude"] == -0.1


def test_ohid_mapping_rejects_missing_project_indicator(tmp_path):
    source_path = tmp_path / "incomplete_fingertips_extract.csv"
    pd.DataFrame(
        [
            {
                "Area Code": "AREA001",
                "Area Name": "Demo Area",
                "Indicator Name": "Saturated fat proxy index",
                "Value": 62.0,
                "Latitude": 51.5,
                "Longitude": -0.1,
            }
        ]
    ).to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        map_ohid_fingertips_indicator_csv(source_path)


def test_ohid_mapping_rejects_duplicate_area_indicator_rows(tmp_path):
    source_path = tmp_path / "duplicate_fingertips_extract.csv"
    pd.DataFrame(
        [
            {
                "Area Code": "AREA001",
                "Area Name": "Demo Area",
                "Indicator Name": "Saturated fat proxy index",
                "Value": 62.0,
                "Latitude": 51.5,
                "Longitude": -0.1,
            },
            {
                "Area Code": "AREA001",
                "Area Name": "Demo Area",
                "Indicator Name": "Saturated fat proxy index",
                "Value": 64.0,
                "Latitude": 51.5,
                "Longitude": -0.1,
            },
        ]
    ).to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="Duplicate OHID/Fingertips source rows"):
        map_ohid_fingertips_indicator_csv(source_path)
