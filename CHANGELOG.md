# Changelog

All notable changes to this portfolio MVP are documented here.

This project follows a lightweight release-note format rather than strict semantic versioning because it is a portfolio demonstration, not a production package.

## Unreleased

### Added

- Case study document covering product decisions, trade-offs, safety boundaries and interview narrative.
- Data quality report layer for aggregate input validation summaries in code, dashboard and docs.

## v0.1.0 - 2026-05-20

First public portfolio MVP release.

### Added

- Live Streamlit dashboard deployment.
- Synthetic aggregate prescribing dataset with four medication classes:
  - NSAID
  - Antihypertensive
  - Lipid-lowering
  - Antidiabetic
- Synthetic public-health indicator dataset for area-level context.
- Streamlit dashboard with:
  - disclaimer and safe-use boundary
  - regional prevention-prioritisation ranking
  - geographic map view
  - risk-tier and primary-planning-signal map colouring
  - selected-area medication-class trend
  - score component breakdown
  - public-health indicator snapshot
  - non-clinical regional Markdown report export
- Transparent weighted composite scoring method.
- Primary planning-signal explanation layer for map and area review.
- Connector stubs for future OpenPrescribing-style and OHID/Fingertips-style aggregate data.
- Data validation checks for aggregate prescribing and public-health inputs.
- Test suite covering connector, validation, scoring, reporting and planning-signal logic.
- GitHub Actions workflow for pytest.
- Documentation set:
  - model card
  - architecture overview
  - scoring methodology
  - data governance notes
  - bias review template
  - ethics and privacy statement
  - deployment notes
  - portfolio pitch
  - demo walkthrough

### Safety boundaries

- Uses synthetic aggregate data by default.
- Does not process patient-level records.
- Does not provide diagnosis, treatment advice, dosing advice, supplement advice or prescribing recommendations.
- Does not claim NHS affiliation, endorsement or approval.
- Frames outputs as public-health planning signals for portfolio demonstration only.

### Known limitations

- Synthetic data cannot support real conclusions about named regions.
- The composite score is illustrative and not clinically validated.
- Connector functions do not make live API calls by default.
- The app does not include production authentication, audit logging, monitoring or deployment governance controls.

### Next candidates

- Optional local downloaded aggregate open-data mapping examples.
- More formal data-quality report output.
- Weight sensitivity analysis.
- GitHub release page with packaged release notes.
