# Forecasting methodology

## Purpose

The forecast layer demonstrates an auditable short-horizon population-health
trend workflow. It is not a clinical prediction model and is not intended to
forecast an individual's health, diagnose disease or set budgets.

## Model

For each area and indicator, `src/regional_forecasting.py`:

1. Converts years and values to numeric observations.
2. Removes missing values and retains the latest value for duplicate years.
3. Requires at least four annual observations.
4. Fits ordinary least squares to at most the six most recent observations.
5. Projects only the next two periods.
6. Clips prevalence projections to the valid 0-100 percentage range.

For year `t`, the fitted model is:

```text
y(t) = intercept + slope * (t - first_training_year)
```

The short window is a modelling choice, not an assertion that older history is
irrelevant. It keeps the result responsive to recent patterns while limiting
long-range extrapolation.

## Diagnostics

Each output records:

- training start and end year
- number of observations
- slope in percentage points per year
- in-sample R-squared
- rolling-origin mean absolute error (MAE)
- rolling-origin symmetric mean absolute percentage error (sMAPE)
- a descriptive recent-linear-fit label

The labels are based on observation count, in-sample fit and rolling sMAPE. They
are interface summaries, not calibrated probabilities or validation grades.

## Exploratory interval

The displayed band uses `1.28 * error_scale * sqrt(horizon)`, where the error
scale is the largest of training residual RMSE, rolling MAE and 0.01. The factor
1.28 approximates an 80% normal interval. Bounds are clipped to 0-100 and kept
ordered around the displayed projection.

This is a residual-variation band. It does not capture policy changes, coding
changes, survey redesign, service disruption, demographic shifts, structural
breaks or uncertainty in future covariates. It must not be interpreted as a
formal prediction interval with guaranteed coverage.

## Backtesting

Rolling-origin backtesting begins once three prior observations are available.
At each step, the model trains only on earlier observations and predicts the
next recorded year. The process avoids training on the target value, but short
series still produce sparse evidence. Indicators with fewer than four total
observations are shown without a forecast.

## Known limitations

- Linear trends can miss plateaus, reversals and shocks.
- Annual observations may not be equally spaced for every indicator.
- Prevalence can change because of detection, coding, denominator or policy.
- UK QOF and US BRFSS/CDI values are not exchangeable outcomes.
- No population weighting, age modelling for QOF, spatial dependence or
  covariate adjustment is included.
- Model selection was not tuned against a held-out regional benchmark.

## Future validation path

Before operational use, compare naive-last-value, drift, regularised time-series
and hierarchical models through blocked temporal validation. Report calibration
and coverage by indicator and geography, test definition breaks, add demographic
and policy covariates only with a pre-specified rationale, and complete bias,
public-health and governance review.
