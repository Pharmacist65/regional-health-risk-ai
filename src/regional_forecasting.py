"""Transparent short-horizon forecasts for aggregate regional indicators.

The helpers in this module are intentionally small and auditable. They are for
portfolio-scale public-health planning exploration, not clinical prediction or
individual decision support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastPoint:
    """One projected aggregate value and an exploratory uncertainty interval."""

    year: int
    value: float
    lower: float
    upper: float


@dataclass(frozen=True)
class TrendForecast:
    """Result of a transparent recent-window linear trend model."""

    model_name: str
    observations: int
    training_start_year: int
    training_end_year: int
    slope_per_year: float
    r_squared: float
    backtest_mae: float | None
    backtest_smape_pct: float | None
    quality: str
    points: tuple[ForecastPoint, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "observations": self.observations,
            "training_start_year": self.training_start_year,
            "training_end_year": self.training_end_year,
            "slope_per_year": self.slope_per_year,
            "r_squared": self.r_squared,
            "backtest_mae": self.backtest_mae,
            "backtest_smape_pct": self.backtest_smape_pct,
            "quality": self.quality,
            "points": [point.__dict__ for point in self.points],
        }


def _clean_series(years: Iterable[object], values: Iterable[object]) -> pd.DataFrame:
    frame = pd.DataFrame({"year": list(years), "value": list(values)})
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna().sort_values("year").drop_duplicates("year", keep="last")
    frame["year"] = frame["year"].astype(int)
    return frame.reset_index(drop=True)


def _fit_line(frame: pd.DataFrame) -> tuple[float, float, float, float, float]:
    x = frame["year"].to_numpy(dtype=float)
    y = frame["value"].to_numpy(dtype=float)
    x_origin = float(x[0])
    x_centered = x - x_origin
    slope, intercept = np.polyfit(x_centered, y, deg=1)
    fitted = intercept + slope * x_centered
    residuals = y - fitted
    residual_rmse = float(np.sqrt(np.mean(np.square(residuals))))
    total_variation = float(np.sum(np.square(y - y.mean())))
    residual_variation = float(np.sum(np.square(residuals)))
    r_squared = 1.0 if total_variation == 0 else max(0.0, 1 - residual_variation / total_variation)
    return float(slope), float(intercept), x_origin, r_squared, residual_rmse


def _rolling_backtest(frame: pd.DataFrame, window: int) -> tuple[float | None, float | None]:
    errors: list[float] = []
    smape_values: list[float] = []
    for target_index in range(3, len(frame)):
        training = frame.iloc[max(0, target_index - window) : target_index]
        slope, intercept, x_origin, _, _ = _fit_line(training)
        actual = float(frame.iloc[target_index]["value"])
        target_year = float(frame.iloc[target_index]["year"])
        predicted = intercept + slope * (target_year - x_origin)
        errors.append(abs(actual - predicted))
        denominator = abs(actual) + abs(predicted)
        if denominator > 0:
            smape_values.append(200 * abs(actual - predicted) / denominator)

    mae = float(np.mean(errors)) if errors else None
    smape = float(np.mean(smape_values)) if smape_values else None
    return mae, smape


def _quality_label(observations: int, r_squared: float, smape: float | None) -> str:
    if observations >= 6 and r_squared >= 0.65 and smape is not None and smape <= 5:
        return "Stronger recent linear fit"
    if observations >= 4 and smape is not None and smape <= 12:
        return "Moderate recent linear fit"
    return "Exploratory recent linear fit"


def forecast_recent_trend(
    years: Iterable[object],
    values: Iterable[object],
    *,
    future_years: Iterable[int],
    window: int = 6,
    bounds: tuple[float, float] | None = None,
    interval_z: float = 1.28,
) -> TrendForecast:
    """Fit a recent-window linear trend and project specified future years.

    The interval is an exploratory 80% residual-based band. It does not capture
    policy shocks, definition changes, survey redesign, or other structural
    uncertainty.
    """
    frame = _clean_series(years, values)
    if len(frame) < 4:
        raise ValueError("At least four numeric annual observations are required.")
    if window < 4:
        raise ValueError("Forecast window must include at least four observations.")

    training = frame.tail(window).copy()
    slope, intercept, x_origin, r_squared, residual_rmse = _fit_line(training)
    backtest_mae, backtest_smape = _rolling_backtest(frame, window)
    interval_scale = max(residual_rmse, backtest_mae or 0.0, 0.01)
    last_year = int(training["year"].max())

    points: list[ForecastPoint] = []
    for year in sorted(set(int(value) for value in future_years)):
        if year <= last_year:
            raise ValueError("Future years must be later than the final observation year.")
        horizon = year - last_year
        estimate = intercept + slope * (year - x_origin)
        margin = interval_z * interval_scale * np.sqrt(horizon)
        lower = estimate - margin
        upper = estimate + margin
        if bounds is not None:
            estimate = min(bounds[1], max(bounds[0], estimate))
            lower = min(estimate, max(bounds[0], min(bounds[1], lower)))
            upper = max(estimate, min(bounds[1], max(bounds[0], upper)))
        points.append(
            ForecastPoint(
                year=year,
                value=round(float(estimate), 2),
                lower=round(float(lower), 2),
                upper=round(float(upper), 2),
            )
        )

    return TrendForecast(
        model_name="Recent-window ordinary least squares",
        observations=len(training),
        training_start_year=int(training["year"].min()),
        training_end_year=last_year,
        slope_per_year=round(slope, 3),
        r_squared=round(r_squared, 3),
        backtest_mae=None if backtest_mae is None else round(backtest_mae, 3),
        backtest_smape_pct=(
            None if backtest_smape is None else round(backtest_smape, 2)
        ),
        quality=_quality_label(len(training), r_squared, backtest_smape),
        points=tuple(points),
    )


__all__ = ["ForecastPoint", "TrendForecast", "forecast_recent_trend"]
