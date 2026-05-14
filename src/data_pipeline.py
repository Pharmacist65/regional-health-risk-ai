"""Data preparation helpers for the Regional Health Risk Optimisation MVP.

The project can run on synthetic demo data included in the repository.
For real analysis, replace the demo data with aggregate open datasets such as
NHSBSA English Prescribing Data, OpenPrescribing, and OHID Fingertips.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


AREAS = [
    ("E09000007", "Camden", 51.5290, -0.1255),
    ("E09000012", "Hackney", 51.5450, -0.0553),
    ("E09000030", "Tower Hamlets", 51.5099, -0.0059),
    ("E09000025", "Newham", 51.5077, 0.0469),
    ("E08000003", "Manchester", 53.4808, -2.2426),
    ("E08000025", "Birmingham", 52.4862, -1.8904),
    ("E08000035", "Leeds", 53.8008, -1.5491),
    ("E06000023", "Bristol", 51.4545, -2.5879),
]

MEDICATION_CLASSES = ["NSAID", "Antihypertensive", "Lipid-lowering", "Antidiabetic"]


def generate_demo_data(output_dir: str | Path = "data") -> None:
    """Generate synthetic aggregate data for local demos.

    The generated values are not real NHS data and must not be interpreted as
    local health evidence. They exist only to demonstrate the software flow.
    """
    rng = np.random.default_rng(seed=42)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    prescribing_rows = []
    public_health_rows = []

    base_area_risk = {
        "Camden": 0.45,
        "Hackney": 0.62,
        "Tower Hamlets": 0.70,
        "Newham": 0.78,
        "Manchester": 0.72,
        "Birmingham": 0.68,
        "Leeds": 0.55,
        "Bristol": 0.42,
    }

    for area_code, area_name, lat, lon in AREAS:
        area_risk = base_area_risk[area_name]
        public_health_rows.append(
            {
                "area_code": area_code,
                "area_name": area_name,
                "latitude": lat,
                "longitude": lon,
                "saturated_fat_proxy_index": round(40 + 45 * area_risk + rng.normal(0, 4), 1),
                "deprivation_index": round(20 + 60 * area_risk + rng.normal(0, 5), 1),
                "obesity_prevalence_pct": round(18 + 18 * area_risk + rng.normal(0, 2), 1),
                "hypertension_prevalence_estimate_pct": round(10 + 14 * area_risk + rng.normal(0, 1.5), 1),
                "diabetes_prevalence_estimate_pct": round(4 + 8 * area_risk + rng.normal(0, 1), 1),
            }
        )

        for month in months:
            seasonal = 1 + 0.10 * np.sin((month.month / 12) * 2 * np.pi)
            for med_class in MEDICATION_CLASSES:
                if med_class == "NSAID":
                    baseline = 70 + 45 * area_risk
                elif med_class == "Antihypertensive":
                    baseline = 95 + 80 * area_risk
                elif med_class == "Lipid-lowering":
                    baseline = 80 + 65 * area_risk
                else:
                    baseline = 45 + 50 * area_risk
                items = max(5, baseline * seasonal + rng.normal(0, 7))
                cost = items * rng.uniform(1.5, 4.5)
                prescribing_rows.append(
                    {
                        "month": month.strftime("%Y-%m-%d"),
                        "area_code": area_code,
                        "area_name": area_name,
                        "medication_class": med_class,
                        "items_per_1000": round(items, 2),
                        "cost_per_1000": round(cost, 2),
                    }
                )

    pd.DataFrame(prescribing_rows).to_csv(output_path / "sample_aggregate_prescribing.csv", index=False)
    pd.DataFrame(public_health_rows).to_csv(output_path / "sample_public_health_indicators.csv", index=False)


if __name__ == "__main__":
    generate_demo_data()
