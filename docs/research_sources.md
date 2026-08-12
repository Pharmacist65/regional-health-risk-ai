# Research sources and comparability

## Scope

The regional explorer uses official aggregate sources to show separate England
and United States views. The first UK release deliberately uses the nine English
statistical regions because Scotland, Wales and Northern Ireland publish through
different health systems and definitions. Combining them into one apparent UK
league table would create false comparability.

The source snapshot was extracted on 2026-08-12. Source publication periods are
shown in the data rather than replaced with the extract date.

## Freshness and historical depth

The snapshot was rechecked against the publishers on 2026-08-12. "Full
history" means the longest currently published series that preserves the
selected measure, population and geography. It does not mean concatenating
archived tables after a definition or boundary change.

| Source | Publisher status on 2026-08-12 | History used in this project | Decision |
| --- | --- | --- | --- |
| NHS England QOF / OHID Fingertips | 2024/25 is the latest release; 2025/26 is scheduled for 27 August 2026 | 2012/13-2024/25 for most selected indicators; depression has 12 periods and asthma starts in 2020/21 | Retain the complete statistical-region history returned for each current indicator definition |
| ONS Health Index | Current edition released 16 June 2023; next release to be announced | 2015-2021 | Retain the complete current edition |
| HM Treasury CRA 2025 | Current release covers 2020/21-2024/25 | 2020/21-2024/25 | Retain the complete current-vintage table; do not splice older rolling releases across revisions |
| CDC Chronic Disease Indicators | Dataset updated 4 June 2026 and contains source years through 2023 | 2019-2023 for the selected refreshed indicators; hypertension is biennial | Retain every available overall age-adjusted observation for the selected current indicator IDs |
| CMS State Health Expenditure Accounts | Current state-of-residence release is 1991-2020 | 1991-2020 | Retain the complete 30-year residence series |

NHS England has QOF archives back to 2004/05, but indicator definitions,
denominators and published regional geographies changed. The earlier archive is
therefore a candidate for a separately versioned harmonisation study, not an
automatic extension of the present chart. The same rule applies to retired CDC
CDI releases and older HM Treasury rolling vintages.

## Health history

### England

[OHID Fingertips](https://fingertips.phe.org.uk/) provides regional QOF
registered-prevalence histories for hypertension, diabetes, COPD, coronary heart
disease, cancer, depression and asthma. QOF measures recorded prevalence among
registered populations; indicator-specific age denominators are retained.

The [ONS Health Index](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/healthandwellbeing/datasets/healthindexscoresengland)
adds a broader historical context series for 2015-2021. It is stored in the
official data layer but is not treated as a disease prevalence measure.

### United States

[CDC Chronic Disease Indicators](https://data.cdc.gov/d/hksd-2xuw) provides
state-level age-adjusted adult prevalence estimates for current asthma, high
blood pressure, COPD, diabetes, depression and obesity. The current explorer
uses overall estimates for the 50 states and District of Columbia and groups
states into the eight CMS regions for navigation context. Although the full CDC
table contains source years from 2015, the selected refreshed indicators begin
in 2019; no retired definition is backfilled into those series.

## Spending history

[HM Treasury Country and Regional Analysis 2025](https://www.gov.uk/government/statistics/country-and-regional-analysis-2025)
provides identifiable public expenditure on health per head for English regions
from 2020/21 through 2024/25.

[CMS State Health Expenditure Accounts](https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/state-residence)
provides all-payer personal health care expenditure per capita by state of
residence from 1991 through 2020.

The two spending series differ in scope, currency, accounting basis and period.
They are contextual trends inside each country, not a cross-country efficiency
comparison. Values are nominal and are not inflation adjusted in this release.

## Display geography

The 3D atlas uses a separate, display-only geography bundle. Boundary geometry
does not contribute to health values, ranks, forecasts or hypotheses.

- [Natural Earth 1:110m Admin 0 countries](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/)
  provides the world context. Natural Earth vector data is public domain.
- [US Census TIGERweb](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer)
  provides January 1, 2025 state boundaries. The bundle retains the 50 states
  and District of Columbia and excludes US territories because they are not in
  the current health-data view.
- [ONS Regions (December 2024) Boundaries EN BFC](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Regions_December_2024_Boundaries_EN_BFC/FeatureServer)
  provides the nine English statistical-region shapes.

The committed geometry is simplified for browser rendering and must not be used
as a legal or survey boundary. ONS digital boundaries are supplied under the
[Open Government Licence v3.0](https://www.ons.gov.uk/methodology/geography/licences).
Required attribution: Source: Office for National Statistics licensed under the
Open Government Licence v.3.0. Contains OS data &copy; Crown copyright and
database right 2024.

## Comparability matrix

| Dimension | England view | United States view | Dashboard rule |
| --- | --- | --- | --- |
| Geography | Nine English statistical regions | 50 states and District of Columbia | Select and rank within country only |
| Health measure | QOF registered prevalence | BRFSS/CDI age-adjusted adult prevalence | Never form a cross-country rank |
| Denominator | Indicator-specific registered population | Adults aged 18+, age adjusted | Display beside every selected metric |
| Spending | Identifiable public health expenditure per head | All-payer personal health care expenditure per capita | Separate currency and definition |
| Forecast | Recent-window OLS, two periods | Recent-window OLS, two years | Exploratory trend only |

## Contribution-hypothesis evidence

The interface offers research prompts for domains that may contribute to
regional patterns. A prompt is not a finding, attributable fraction or claim
about a community.

- Diabetes: [CDC diabetes risk factors](https://www.cdc.gov/diabetes/risk-factors/)
- Hypertension: [CDC high blood pressure overview](https://www.cdc.gov/high-blood-pressure/about/)
- COPD: [CDC COPD overview](https://www.cdc.gov/copd/about/index.html) and [NIOSH occupational COPD](https://www.cdc.gov/niosh/bulletin/2020/copd.html)
- Coronary heart disease: [CDC heart disease facts](https://www.cdc.gov/heart-disease/data-research/facts-stats/)
- Cancer: [NCI cancer statistics types](https://seer.cancer.gov/statistics/types.html) and [NCI screening overview](https://www.cancer.gov/about-cancer/screening)
- Asthma: [CDC asthma risk factors](https://www.cdc.gov/asthma/risk-factors/)
- Depression: [CDC mental health](https://www.cdc.gov/mental-health/about/)
- Obesity: [CDC obesity risk factors](https://www.cdc.gov/obesity/risk-factors/risk-factors.html)

Candidate domains include age structure, detection and register completeness,
smoking history, occupational and air exposures, obesity, physical activity,
deprivation, screening and access. The current model does not estimate causal
effects for any of them.

## Review questions before extension

1. Is the proposed measure stable across the selected years and geographies?
2. Are denominator, age adjustment, survey or register definitions preserved?
3. Could higher prevalence reflect detection or recording differences?
4. Are uncertainty intervals and missing periods visible?
5. Does a proposed explanation require covariate, lag or causal-design analysis?
6. Can the output remain aggregate, non-clinical and non-stigmatising?
