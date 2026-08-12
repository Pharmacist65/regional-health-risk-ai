# Research sources and comparability

## Scope

The regional explorer uses official aggregate sources to show separate England
and United States views. The first UK release deliberately uses the nine English
statistical regions because Scotland, Wales and Northern Ireland publish through
different health systems and definitions. Combining them into one apparent UK
league table would create false comparability.

The source snapshot was extracted on 2026-08-13. Source publication periods are
shown in the data rather than replaced with the extract date.

## Freshness and historical depth

The snapshot was rechecked against the publishers on 2026-08-13. "Full
history" means the longest currently published series that preserves the
selected measure, population and geography. It does not mean concatenating
archived tables after a definition or boundary change.

| Source | Publisher status on 2026-08-13 | History used in this project | Decision |
| --- | --- | --- | --- |
| NHS England QOF / OHID Fingertips | 2024/25 is the latest release; 2025/26 is scheduled for 27 August 2026 | 2012/13-2024/25 for most selected indicators; depression has 12 periods and asthma starts in 2020/21 | Retain the complete statistical-region history returned for each current indicator definition |
| ONS Health Index | Current edition released 16 June 2023; next release to be announced | 2015-2021 | Retain the complete current edition |
| HM Treasury CRA 2025 | Current release covers 2020/21-2024/25 | 2020/21-2024/25 | Retain the complete current-vintage table; do not splice older rolling releases across revisions |
| CDC Chronic Disease Indicators | Dataset updated 4 June 2026 and contains source years through 2023 | 2019-2023 for the selected refreshed indicators; hypertension is biennial | Retain every available overall age-adjusted observation for the selected current indicator IDs |
| CMS State Health Expenditure Accounts | Current state-of-residence release is 1991-2020 | 1991-2020 | Retain the complete 30-year residence series |
| ONS population estimates | Mid-2024 is the latest complete estimate used for English regions | Mid-2024 | Use as the resident-population denominator for access density |
| CQC care directory | Directory dated 12 August 2026 | Current directory snapshot | Select locations carrying hospital or Doctors/GP service types |
| NHSBSA pharmaceutical list | 2026/27 Q1 resource published 29 July 2026 | Current contract snapshot | Select Community and Local Pharmaceutical Services entries |
| U.S. Census state population estimates | Vintage 2025 state detail | 2025 total/adult and revised 2023 adult estimates | Use 2025 for current access density and 2023 for CDC burden estimation |
| CMS Hospital General Information | File updated 28 April 2026 | Current directory snapshot | Retain hospitals in the 50 states and District of Columbia |
| HRSA health centers and HPSAs | Files created 12 August 2026 | Current directory and designation snapshots | Retain active service sites and designated primary-care HPSAs |
| NPPES NPI Registry | Public API queried 13 August 2026 | Query-date snapshot | Retain active organization NPIs with the Community/Retail Pharmacy taxonomy and primary practice address in the state |

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

## Population burden

The disease charts remain rate-first so areas of different size can be compared
within the same country and measure.

For England, the latest burden value is the official QOF disease-register count
and uses the metric-specific registered-patient denominator supplied by OHID.
It is therefore not inferred from the ONS resident-population estimate.

For the United States, CDC publishes age-adjusted values for comparison and
crude values for population burden. The dashboard keeps the age-adjusted value
in the trend and peer views, then multiplies the latest 2023 crude prevalence by
the revised 2023 Census resident population aged 18+. The displayed range
applies the CDC crude-prevalence confidence limits to the same denominator.
This produces a transparent planning estimate rather than a surveillance case
count.

## Healthcare access directories

England access records use:

- CQC locations with a `Hospital` or `Hospitals - Mental health/capacity`
  service type for the hospital category
- CQC locations with a `Doctors/GPs` service type for primary care
- NHSBSA Community and Local Pharmaceutical Services contract entries for
  pharmacies

United States access records use:

- hospitals in CMS Hospital General Information
- active HRSA Health Center Service Delivery and Look-Alike sites, excluding
  administrative-only sites, for the primary-care category
- active organization NPIs with taxonomy `3336C0003X` and a primary practice
  address in the state for community/retail pharmacy directory records
- designated HRSA Primary Care Health Professional Shortage Areas for a
  separate shortage-context signal

Counts are divided by the latest resident-population estimate and displayed per
100,000 residents. The same-country median marker is descriptive and does not
declare an area adequately or inadequately served. Directory status, service
availability, appointment capacity, travel time and licensure are distinct
questions and should be evaluated with the relevant operational source.

CQC and NHSBSA publish the selected directory data under the Open Government
Licence v3.0. HRSA lists no usage limitations for the selected health-center and
HPSA downloads. NPPES exposes FOIA-disclosable provider fields; CMS states that
an NPI does not by itself validate licensure or credentials. The committed
NPPES subset excludes authorized-official fields.

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
| Burden count | Exact QOF register count | CDC crude prevalence applied to same-year Census adult population | Label exact and modelled values separately |
| Population for access density | ONS mid-2024 residents | Census Vintage 2025 residents | Calculate within the selected geography |
| Care directory categories | CQC hospital/Doctors-GP locations and NHSBSA pharmacy contracts | CMS hospitals, HRSA health centers and NPPES pharmacy organizations | Keep publisher definitions visible; do not merge into one score |
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
