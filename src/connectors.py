"""Connector stubs for future aggregate open-data integration.

The project runtime intentionally defaults to synthetic local CSV files. These
helpers document the future connector boundary for OpenPrescribing-style
aggregate prescribing data and OHID/Fingertips-style public-health indicators.

No function in this module makes live API calls by default, requires API keys,
or handles patient-level data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.validation import (
    PRESCRIBING_REQUIRED_COLUMNS,
    PUBLIC_HEALTH_REQUIRED_COLUMNS,
    validate_prescribing_data,
    validate_public_health_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_PRESCRIBING_PATH = DATA_DIR / "sample_aggregate_prescribing.csv"
SYNTHETIC_PUBLIC_HEALTH_PATH = DATA_DIR / "sample_public_health_indicators.csv"

OPENPRESCRIBING_AGGREGATE_COLUMNS = PRESCRIBING_REQUIRED_COLUMNS
OHID_FINGERTIPS_INDICATOR_COLUMNS = PUBLIC_HEALTH_REQUIRED_COLUMNS


@dataclass(frozen=True)
class ConnectorResult:
    """Structured result returned by connector stubs.

    Attributes
    ----------
    name:
        Stable connector identifier.
    data:
        Aggregate, area-level data frame ready for the existing pipeline.
    source:
        Local file path or future source descriptor.
    is_live_call:
        Always false for the current stubs. This prevents accidental API use in
        the public portfolio project.
    expected_columns:
        Column contract the downstream pipeline expects.
    notes:
        Human-readable governance and implementation notes.
    """

    name: str
    data: pd.DataFrame
    source: str
    is_live_call: bool
    expected_columns: tuple[str, ...]
    notes: str


def _read_local_csv(path: str | Path) -> pd.DataFrame:
    """Read a local aggregate CSV file."""
    csv_path = Path(path)
    return pd.read_csv(csv_path)


def load_openprescribing_aggregate_prescribing(
    source_path: str | Path | None = None,
    *,
    use_live_api: bool = False,
) -> ConnectorResult:
    """Return OpenPrescribing-style aggregate prescribing data.

    This is a documented placeholder for a future OpenPrescribing/NHSBSA-style
    aggregate prescribing connector. The current implementation reads the
    synthetic sample prescribing CSV unless a caller supplies another local CSV
    path with the same aggregate schema.

    Parameters
    ----------
    source_path:
        Optional local CSV override for tests or future offline fixtures.
    use_live_api:
        Reserved for a future implementation. Passing true raises
        ``NotImplementedError`` so the app never makes live API calls
        accidentally.
    """
    if use_live_api:
        raise NotImplementedError(
            "Live OpenPrescribing API access is intentionally not implemented. "
            "Use local aggregate CSV data until governance, validation and "
            "fallback behaviour are documented."
        )

    path = Path(source_path) if source_path is not None else SYNTHETIC_PRESCRIBING_PATH
    data = _read_local_csv(path)
    validate_prescribing_data(data)
    return ConnectorResult(
        name="openprescribing_aggregate_prescribing_stub",
        data=data,
        source=str(path),
        is_live_call=False,
        expected_columns=OPENPRESCRIBING_AGGREGATE_COLUMNS,
        notes=(
            "Placeholder connector returning synthetic aggregate prescribing "
            "data. No API keys, live calls or patient-level records are used."
        ),
    )


def load_ohid_fingertips_public_health_indicators(
    source_path: str | Path | None = None,
    *,
    use_live_api: bool = False,
) -> ConnectorResult:
    """Return OHID/Fingertips-style aggregate public-health indicators.

    This is a documented placeholder for a future OHID Fingertips connector. The
    current implementation reads the synthetic public-health indicator CSV
    unless a caller supplies another local CSV path with the same aggregate
    schema.

    Parameters
    ----------
    source_path:
        Optional local CSV override for tests or future offline fixtures.
    use_live_api:
        Reserved for a future implementation. Passing true raises
        ``NotImplementedError`` so the app never makes live API calls
        accidentally.
    """
    if use_live_api:
        raise NotImplementedError(
            "Live OHID/Fingertips API access is intentionally not implemented. "
            "Use local aggregate CSV data until governance, validation and "
            "fallback behaviour are documented."
        )

    path = Path(source_path) if source_path is not None else SYNTHETIC_PUBLIC_HEALTH_PATH
    data = _read_local_csv(path)
    validate_public_health_data(data)
    return ConnectorResult(
        name="ohid_fingertips_public_health_stub",
        data=data,
        source=str(path),
        is_live_call=False,
        expected_columns=OHID_FINGERTIPS_INDICATOR_COLUMNS,
        notes=(
            "Placeholder connector returning synthetic aggregate public-health "
            "indicators. No API keys, live calls or patient-level records are used."
        ),
    )
