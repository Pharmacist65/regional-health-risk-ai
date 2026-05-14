# Scoring methodology

## Summary

The project uses a transparent weighted composite score over aggregate area-level indicators. It is intentionally simple because the goal is to demonstrate interpretable public-health analytics, not a black-box clinical prediction model.

## Inputs

The score uses:

- mean NSAID items per 1,000 population
- combined cardiometabolic prescribing density
- saturated-fat proxy index
- deprivation index
- obesity prevalence estimate

All inputs are synthetic in the default dataset.

## Scaling

Each input is min-max scaled across the loaded regions. This produces a 0 to 1 signal for each component and keeps the demo easy to inspect.

Min-max scaling is useful for a portfolio MVP because it is transparent, but it has limitations:

- it depends on the regions currently loaded
- outliers can compress the rest of the scale
- it does not estimate uncertainty
- it is not a clinical calibration method

## Weights

Current illustrative weights:

| Component | Weight |
| --- | ---: |
| NSAID persistence signal | 35% |
| Cardiometabolic prescribing density | 25% |
| Saturated-fat proxy index | 20% |
| Deprivation index | 10% |
| Obesity prevalence estimate | 10% |

The weights are not clinically validated. They are visible in the app and model card so reviewers can challenge the assumptions.

## What the score is

The score is a prevention-prioritisation signal for aggregate planning conversations. It can help demonstrate how a team might rank areas for awareness materials, pharmacy signposting or further public-health review.

## What the score is not

The score is not:

- an individual risk score
- a diagnosis
- a treatment recommendation
- a prescribing or dosing tool
- a cost-saving claim
- evidence of actual local health need

## Validation required for real-world use

A real implementation would need:

- clear outcome or planning objective
- stakeholder review of indicator selection
- sensitivity analysis for weights
- assessment of confounding and demographic structure
- fairness and bias review
- external validation against appropriate aggregate outcomes
- monitoring for drift and data-quality failures
