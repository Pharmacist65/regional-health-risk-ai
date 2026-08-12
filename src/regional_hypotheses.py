"""Evidence-linked contribution hypotheses for aggregate regional signals.

These are prompts for further investigation. They are not causal findings and
must not be presented as explanations for any individual or community.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HypothesisTemplate:
    title: str
    investigation_prompt: str
    interpretation_guardrail: str
    evidence_url: str


HYPOTHESES_BY_METRIC: dict[str, tuple[HypothesisTemplate, ...]] = {
    "diabetes": (
        HypothesisTemplate(
            title="Age and population structure",
            investigation_prompt=(
                "Check whether older age composition helps explain the observed aggregate "
                "prevalence pattern."
            ),
            interpretation_guardrail=(
                "Age is a known risk factor; source-specific age adjustment does not remove "
                "all contextual confounding."
            ),
            evidence_url="https://www.cdc.gov/diabetes/risk-factors/",
        ),
        HypothesisTemplate(
            title="Obesity and physical activity context",
            investigation_prompt=(
                "Compare obesity, physical activity, food access and deprivation indicators "
                "before prioritising prevention research."
            ),
            interpretation_guardrail="Co-occurrence at area level does not establish causality.",
            evidence_url="https://www.cdc.gov/diabetes/risk-factors/",
        ),
    ),
    "hypertension": (
        HypothesisTemplate(
            title="Detection and recording intensity",
            investigation_prompt=(
                "Review screening, diagnosis and recording completeness alongside "
                "the prevalence signal."
            ),
            interpretation_guardrail=(
                "Higher measured prevalence can partly reflect detection and recording."
            ),
            evidence_url="https://www.cdc.gov/high-blood-pressure/about/",
        ),
        HypothesisTemplate(
            title="Cardiometabolic context",
            investigation_prompt=(
                "Examine obesity, physical inactivity, diabetes and age structure as candidate "
                "contextual contributors."
            ),
            interpretation_guardrail="These are population-level research prompts, not patient risk factors.",
            evidence_url="https://www.cdc.gov/high-blood-pressure/about/",
        ),
    ),
    "copd": (
        HypothesisTemplate(
            title="Smoking history",
            investigation_prompt=(
                "Compare current and historical tobacco exposure with respiratory prevalence."
            ),
            interpretation_guardrail="The dashboard does not estimate attributable fractions.",
            evidence_url="https://www.cdc.gov/copd/about/index.html",
        ),
        HypothesisTemplate(
            title="Air and occupational exposures",
            investigation_prompt=(
                "Review air quality and the regional mix of occupations involving dust, fumes "
                "or other respiratory hazards."
            ),
            interpretation_guardrail="Exposure data are not included in the current model.",
            evidence_url="https://www.cdc.gov/niosh/bulletin/2020/copd.html",
        ),
    ),
    "chd": (
        HypothesisTemplate(
            title="Cardiometabolic risk-factor mix",
            investigation_prompt=(
                "Assess hypertension, diabetes, smoking, obesity and age structure together."
            ),
            interpretation_guardrail="A regional association cannot identify an individual's cause.",
            evidence_url="https://www.cdc.gov/heart-disease/data-research/facts-stats/",
        ),
        HypothesisTemplate(
            title="Access and deprivation context",
            investigation_prompt=(
                "Review preventive-care access, deprivation and treatment continuity indicators."
            ),
            interpretation_guardrail="Service access is not measured directly in this release.",
            evidence_url="https://www.cdc.gov/heart-disease/about/",
        ),
    ),
    "cancer": (
        HypothesisTemplate(
            title="Age, incidence and survival",
            investigation_prompt=(
                "Separate age structure, new diagnoses and survival before interpreting a "
                "registered prevalence difference."
            ),
            interpretation_guardrail="Prevalence is not incidence and may rise when survival improves.",
            evidence_url="https://seer.cancer.gov/statistics/types.html",
        ),
        HypothesisTemplate(
            title="Screening and detection",
            investigation_prompt=(
                "Compare screening uptake and stage-at-diagnosis data before drawing conclusions."
            ),
            interpretation_guardrail="Detection patterns can change measured prevalence.",
            evidence_url="https://www.cancer.gov/about-cancer/screening/patient-screening-overview-pdq",
        ),
    ),
    "asthma": (
        HypothesisTemplate(
            title="Air quality and housing context",
            investigation_prompt=(
                "Review air pollution, damp housing, occupational exposures and smoking context."
            ),
            interpretation_guardrail="These exposures are not measured in the current dataset.",
            evidence_url="https://www.cdc.gov/asthma/about/",
        ),
    ),
    "depression": (
        HypothesisTemplate(
            title="Social and economic context",
            investigation_prompt=(
                "Compare employment, isolation, housing stress and access to mental-health care."
            ),
            interpretation_guardrail="Survey or register prevalence also reflects help-seeking and recording.",
            evidence_url="https://www.cdc.gov/mental-health/about/",
        ),
    ),
    "obesity": (
        HypothesisTemplate(
            title="Food and activity environments",
            investigation_prompt=(
                "Review affordable food access, safe activity space, transport and local design."
            ),
            interpretation_guardrail="Obesity is multifactorial; no single area feature is sufficient.",
            evidence_url="https://www.cdc.gov/obesity/risk-factors/risk-factors.html",
        ),
        HypothesisTemplate(
            title="Economic stability and care access",
            investigation_prompt=(
                "Compare deprivation, economic stability, housing and access to preventive care."
            ),
            interpretation_guardrail="Area-level context should not be used to profile individuals.",
            evidence_url="https://www.cdc.gov/obesity/risk-factors/risk-factors.html",
        ),
    ),
}


def contribution_hypotheses(
    metric_key: str,
    *,
    area_value: float,
    peer_median: float,
) -> list[dict[str, str]]:
    """Return auditable prompts for a metric relative to its country peer median."""
    templates = HYPOTHESES_BY_METRIC.get(metric_key, ())
    if peer_median == 0:
        comparison = "Peer comparison unavailable because the peer median is zero."
    else:
        difference_pct = ((area_value - peer_median) / peer_median) * 100
        direction = "above" if difference_pct >= 0 else "below"
        comparison = f"Observed aggregate value is {abs(difference_pct):.1f}% {direction} the country peer median."

    return [
        {
            "title": template.title,
            "why_surfaced": comparison,
            "investigation_prompt": template.investigation_prompt,
            "guardrail": template.interpretation_guardrail,
            "evidence_url": template.evidence_url,
        }
        for template in templates
    ]


def serialise_hypothesis_registry() -> Mapping[str, list[dict[str, str]]]:
    return {
        metric: [template.__dict__ for template in templates]
        for metric, templates in HYPOTHESES_BY_METRIC.items()
    }


__all__ = [
    "HYPOTHESES_BY_METRIC",
    "HypothesisTemplate",
    "contribution_hypotheses",
    "serialise_hypothesis_registry",
]
