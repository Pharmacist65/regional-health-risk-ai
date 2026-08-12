import pytest

from src.regional_forecasting import forecast_recent_trend


def test_forecast_recent_trend_returns_auditable_projection():
    result = forecast_recent_trend(
        [2018, 2019, 2020, 2021, 2022, 2023],
        [8.0, 8.4, 8.8, 9.2, 9.6, 10.0],
        future_years=[2024, 2025],
        bounds=(0, 100),
    )

    assert result.model_name == "Recent-window ordinary least squares"
    assert result.observations == 6
    assert result.training_start_year == 2018
    assert result.training_end_year == 2023
    assert result.slope_per_year == pytest.approx(0.4)
    assert result.r_squared == pytest.approx(1.0)
    assert [point.year for point in result.points] == [2024, 2025]
    assert result.points[0].value == pytest.approx(10.4)
    assert result.points[0].lower <= result.points[0].value <= result.points[0].upper


def test_forecast_recent_trend_uses_latest_window_and_bounds():
    result = forecast_recent_trend(
        range(2014, 2024),
        [50, 51, 52, 53, 54, 95, 97, 99, 101, 103],
        future_years=[2024],
        window=5,
        bounds=(0, 100),
    )

    assert result.observations == 5
    assert result.training_start_year == 2019
    assert result.points[0].value == 100
    assert result.points[0].upper == 100
    assert result.points[0].lower <= result.points[0].value


def test_forecast_interval_remains_ordered_when_projection_hits_lower_bound():
    result = forecast_recent_trend(
        [2020, 2021, 2022, 2023],
        [3, 2, 1, 0],
        future_years=[2024],
        bounds=(0, 100),
    )

    point = result.points[0]
    assert point.value == 0
    assert point.lower <= point.value <= point.upper


def test_forecast_recent_trend_rejects_insufficient_history():
    with pytest.raises(ValueError, match="At least four"):
        forecast_recent_trend(
            [2021, 2022, 2023],
            [1, 2, 3],
            future_years=[2024],
        )


def test_forecast_recent_trend_rejects_past_projection_year():
    with pytest.raises(ValueError, match="Future years"):
        forecast_recent_trend(
            [2020, 2021, 2022, 2023],
            [1, 2, 3, 4],
            future_years=[2023],
        )
