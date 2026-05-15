# Bias Review Template

## Purpose

Use this template before adapting the project beyond the synthetic portfolio demo. The goal is to identify whether aggregate indicators, score weights or dashboard wording could unfairly frame regions, reinforce stigma or overstate evidence.

This template does not make the score clinically valid. It supports responsible public-health analytics review.

## Review Context

| Item | Notes |
| --- | --- |
| Review date |  |
| Reviewer names / roles |  |
| Dataset version or extract date |  |
| Data sources reviewed |  |
| Intended planning question |  |
| Deployment setting | Portfolio demo / internal prototype / other |
| Real patient-level data used? | Must be no for this project boundary |

## Data Bias Checks

| Check | Pass / concern / not applicable | Notes |
| --- | --- | --- |
| Data is aggregate and non-identifiable |  |  |
| Data provenance and licence are documented |  |  |
| Area coverage is complete for the intended comparison |  |  |
| Missing values are quantified and explained |  |  |
| Outliers are reviewed before scoring |  |  |
| Indicator definitions are consistent across regions |  |  |
| Deprivation or geography proxies are not interpreted as individual traits |  |  |
| Small-area suppression or aggregation thresholds are respected |  |  |

## Score And Method Checks

| Check | Pass / concern / not applicable | Notes |
| --- | --- | --- |
| Score weights are visible to users |  |  |
| Weight choices have a documented rationale |  |  |
| Sensitivity analysis has been run for alternative weights |  |  |
| Min-max scaling effects and outlier sensitivity are documented |  |  |
| The score is not described as diagnosis, treatment advice or clinical prediction |  |  |
| The score is not used to infer need for individual patients |  |  |
| The output includes uncertainty and limitation notes where appropriate |  |  |

## Interpretation And Communication Checks

| Check | Pass / concern / not applicable | Notes |
| --- | --- | --- |
| Dashboard text avoids blaming communities or regions |  |  |
| Region categories are framed as planning signals, not labels of people |  |  |
| Suggested actions remain awareness, signposting or further review categories |  |  |
| No medication changes, dosing advice, supplement advice or treatment recommendations are included |  |  |
| The disclaimer is visible before users interpret the score |  |  |
| Public-health and pharmacy stakeholders have reviewed the wording |  |  |

## Deployment Boundary

Before any non-demo deployment, confirm:

- governance approval is documented
- data protection review is complete
- clinical safety review is complete where relevant
- stakeholder review includes public-health, pharmacy and primary-care perspectives
- monitoring is defined for data drift, missingness and unexpected score changes
- user-facing materials clearly state that the tool is for aggregate planning only

## Review Outcome

| Outcome | Decision |
| --- | --- |
| Approved for current demo use | Yes / no |
| Approved for further prototype testing | Yes / no |
| Requires changes before use | Yes / no |
| Key risks to resolve |  |

## Action Log

| Action | Owner | Due date | Status |
| --- | --- | --- |
|  |  |  |  |
