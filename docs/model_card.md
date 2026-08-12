# Model card

## System name

Regional Preventive Health Analytics portfolio system.

## Components in scope

This model card covers two transparent analytical components:

1. A synthetic aggregate prevention-prioritisation score used by the Streamlit MVP.
2. A recent-window linear trend forecast used by the official regional explorer.

Neither component is a clinical AI system or a validated resource-allocation
model.

## Intended use

- Demonstrate privacy-first population-health data engineering and analytics.
- Explore official aggregate regional histories within the source definition.
- Compare areas only against peers using the same country-level measure.
- Make modelling assumptions, diagnostics and uncertainty visible to reviewers.
- Generate questions for further public-health research, not causal conclusions.

## Prohibited use

- diagnosis, triage, treatment, prescribing or dosing decisions
- individual or household risk prediction
- patient-level clinical decision support
- automated funding, staffing or service-allocation decisions
- ranking UK measures directly against US measures
- claims of NHS, CDC, CMS or government approval or affiliation

## Data

### Official explorer

- England: OHID/NHS England QOF registered prevalence for seven indicators across
  nine statistical regions, plus ONS Health Index context and HM Treasury health
  expenditure per head.
- United States: CDC CDI age-adjusted adult prevalence for six indicators across
  50 states and District of Columbia, plus CMS personal health care expenditure
  per capita.
- All records are aggregate and public. No patient records are used.

QOF registered prevalence and BRFSS/CDI age-adjusted prevalence differ in
denominator, collection and adjustment. Spending series differ in scope,
currency, period and accounting basis.

### Synthetic Streamlit MVP

The original demonstration data contains synthetic area-level medication-class
rates and public-health context indicators. Named geographies do not make those
values evidence about real places.

## Forecast specification

- Model: ordinary least squares on at most six recent observations.
- Minimum history: four numeric annual observations.
- Horizon: two future periods.
- Range: prevalence outputs clipped to 0-100.
- Diagnostics: slope, R-squared, rolling-origin MAE and sMAPE.
- Interval: exploratory 80% residual-variation band.

The band does not include structural uncertainty such as policy, coding,
demographic or survey changes. Fit labels are descriptive summaries, not
calibrated confidence probabilities.

## Synthetic score specification

The Streamlit score uses visible min-max-scaled feature weights:

- NSAID persistence signal: 35%
- cardiometabolic prescribing density: 25%
- saturated-fat proxy index: 20%
- deprivation index: 10%
- obesity prevalence estimate: 10%

Weights are illustrative and not clinically validated.

## Outputs

- observed regional indicator and spending histories
- same-country peer positions
- two-period trend projections where history is sufficient
- model diagnostics and an exploratory uncertainty band
- evidence-linked contribution hypotheses framed as investigation prompts
- synthetic prevention-prioritisation rankings and workflow prompts

## Limitations and risks

- Ecological comparisons cannot explain individual outcomes.
- Higher registered prevalence can partly reflect detection or recording.
- Survey estimates retain sampling and response limitations.
- Linear extrapolation can miss shocks, reversals and plateaus.
- No population weighting, spatial dependence or causal adjustment is included.
- Nominal spending is not adjusted for inflation or local input costs.
- Contribution hypotheses can reinforce stereotypes if presented as findings.
- England-only comparable coverage must not be described as full UK coverage.

## Risk controls

- Source, denominator, period and measure type travel with each metric.
- UK and US views are separated and never cross-ranked.
- Forecasts require minimum history and expose backtest diagnostics.
- Contribution prompts include evidence links and non-causal guardrails.
- Data tests check geography coverage, duplicate keys, value bounds and horizons.
- Public documentation repeats the aggregate-only, non-clinical boundary.

## Validation status

Engineering tests and output-integrity checks are included. No clinical,
epidemiological, economic, fairness or operational validation has been completed.
The system remains a portfolio research preview.
