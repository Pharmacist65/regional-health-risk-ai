from src.regional_hypotheses import (
    contribution_hypotheses,
    serialise_hypothesis_registry,
)


def test_hypotheses_are_relative_and_non_causal():
    hypotheses = contribution_hypotheses(
        "diabetes",
        area_value=12.0,
        peer_median=10.0,
    )

    assert hypotheses
    assert "20.0% above" in hypotheses[0]["why_surfaced"]
    joined = " ".join(str(item) for item in hypotheses).lower()
    assert "does not establish causality" in joined
    assert all(item["evidence_url"].startswith("https://") for item in hypotheses)


def test_unknown_metric_returns_no_invented_hypotheses():
    assert contribution_hypotheses(
        "unknown",
        area_value=1,
        peer_median=1,
    ) == []


def test_shared_hypothesis_templates_do_not_claim_a_country_specific_model():
    registry = serialise_hypothesis_registry()
    guardrails = " ".join(
        item["interpretation_guardrail"]
        for templates in registry.values()
        for item in templates
    ).lower()

    assert "uk qof" not in guardrails
    assert "us brfss" not in guardrails
