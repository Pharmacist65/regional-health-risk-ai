"""Streamlit dashboard for the Regional Health Risk Optimisation MVP."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.connectors import (
    load_ohid_fingertips_public_health_indicators,
    load_openprescribing_aggregate_prescribing,
)
from src.risk_model import (
    add_planning_signal_profiles,
    build_area_features,
    compute_risk_scores,
    format_area_report_markdown,
    public_health_indicator_snapshot,
    score_component_breakdown,
    summarize_area_prescribing,
    summarize_interventions,
)


DATA_DIR = ROOT / "data"
PRESCRIBING_PATH = DATA_DIR / "sample_aggregate_prescribing.csv"
PUBLIC_HEALTH_PATH = DATA_DIR / "sample_public_health_indicators.csv"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    prescribing = load_openprescribing_aggregate_prescribing(PRESCRIBING_PATH).data
    public_health = load_ohid_fingertips_public_health_indicators(PUBLIC_HEALTH_PATH).data
    return prescribing, public_health


st.set_page_config(
    page_title="Regional Preventive Health Analytics",
    layout="wide",
)

prescribing_df, public_health_df = load_data()
features_df = build_area_features(prescribing_df, public_health_df)
scored_df = add_planning_signal_profiles(compute_risk_scores(features_df))
intervention_df = summarize_interventions(scored_df)

TIER_COLORS = {
    "Low": "#2A9D8F",
    "Moderate": "#E9C46A",
    "High": "#F4A261",
    "Very high": "#E76F51",
}
TIER_ORDER = ["Low", "Moderate", "High", "Very high"]
SIGNAL_COLORS = {
    "NSAID safety awareness": "#386641",
    "Cardiometabolic medicines awareness": "#277DA1",
    "Lifestyle context awareness": "#F8961E",
    "Access and communication context": "#6D597A",
    "Weight-related public-health context": "#BC4749",
    "Routine aggregate monitoring": "#8D99AE",
}

st.title("Regional Preventive Health Analytics")
st.markdown(
    "Privacy-first portfolio MVP for exploring population-level prevention priorities "
    "with synthetic aggregate prescribing and public-health indicators."
)

with st.container(border=True):
    st.subheader("Disclaimer and safe-use boundary")
    st.warning(
        "Not affiliated with the NHS. Not medical advice. No patient-level data. "
        "This dashboard is a portfolio proof of concept for aggregate public-health analytics only."
    )
    boundary_cols = st.columns(3)
    boundary_cols[0].markdown("**Data**  \nSynthetic area-level aggregates only.")
    boundary_cols[1].markdown("**Output**  \nInterpretable prevention-prioritisation signals.")
    boundary_cols[2].markdown("**Not for**  \nDiagnosis, dosing, prescribing, or individual decisions.")

st.sidebar.header("Demo controls")
selected_tiers = st.sidebar.multiselect("Risk tiers", TIER_ORDER, default=TIER_ORDER)
selected_area = st.sidebar.selectbox("Area profile", scored_df["area_name"].tolist())
map_colour_mode = st.sidebar.radio(
    "Map colour",
    ["Risk tier", "Primary planning signal"],
    help=(
        "Primary planning signal is the largest weighted aggregate score component. "
        "It is not a disease ranking."
    ),
)
st.sidebar.markdown(
    "Synthetic demo data is loaded from `data/`. The included CSVs are not real NHS or patient records."
)

area_row = scored_df[scored_df["area_name"] == selected_area].iloc[0]
area_rx = prescribing_df[prescribing_df["area_name"] == selected_area].copy()
area_rx["month"] = pd.to_datetime(area_rx["month"])
area_public_health = public_health_df[public_health_df["area_name"] == selected_area].iloc[0]
area_prescribing_summary = summarize_area_prescribing(area_rx)

overview_df = scored_df[scored_df["risk_tier"].isin(selected_tiers)]
if overview_df.empty:
    overview_df = scored_df.copy()

metric_cols = st.columns(4)
metric_cols[0].metric("Areas analysed", f"{scored_df['area_code'].nunique()}")
metric_cols[1].metric("Highest demo score", f"{scored_df['risk_score'].max():.1f}")
metric_cols[2].metric("Medication classes", f"{prescribing_df['medication_class'].nunique()}")
metric_cols[3].metric("Aggregate rows", f"{len(prescribing_df) + len(public_health_df):,}")

overview_tab, area_tab, method_tab = st.tabs(
    ["Regional overview", "Selected area", "Method and governance"]
)

with overview_tab:
    st.subheader("Regional risk overview")
    st.write(
        "Higher scores indicate stronger aggregate signals in this synthetic demo. "
        "They do not represent individual risk or clinical urgency."
    )
    col1, col2 = st.columns([1.2, 1])

    with col1:
        fig = px.bar(
            overview_df,
            x="risk_score",
            y="area_name",
            color="risk_tier",
            color_discrete_map=TIER_COLORS,
            orientation="h",
            hover_data=[
                "risk_tier",
                "nsaid_mean_items_per_1000",
                "cardiometabolic_rx_density",
            ],
            labels={"risk_score": "Composite demo risk score", "area_name": "Area"},
            title="Composite prevention-prioritisation score",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, legend_title_text="Tier")
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("**Geographic planning signals**")
        st.caption(
            "Synthetic area coordinates and indicators only. Primary planning signal reflects "
            "the largest weighted score component, not reported disease counts."
        )
        map_df = overview_df.dropna(subset=["latitude", "longitude"])
        map_color_column = (
            "risk_tier" if map_colour_mode == "Risk tier" else "primary_planning_signal"
        )
        map_color_map = TIER_COLORS if map_color_column == "risk_tier" else SIGNAL_COLORS
        fig = px.scatter_map(
            map_df,
            lat="latitude",
            lon="longitude",
            size="risk_score",
            color=map_color_column,
            color_discrete_map=map_color_map,
            hover_name="area_name",
            hover_data={
                "risk_tier": True,
                "risk_score": ":.1f",
                "primary_planning_signal": True,
                "planning_signal_group": True,
                "hypertension_prevalence_estimate_pct": ":.1f",
                "diabetes_prevalence_estimate_pct": ":.1f",
                "latitude": False,
                "longitude": False,
            },
            zoom=4.7,
            height=440,
            labels={
                "risk_tier": "Risk tier",
                "risk_score": "Demo score",
                "primary_planning_signal": "Primary planning signal",
                "planning_signal_group": "Signal group",
                "hypertension_prevalence_estimate_pct": "Hypertension estimate %",
                "diabetes_prevalence_estimate_pct": "Diabetes estimate %",
            },
        )
        fig.update_layout(
            map_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend_title_text="Tier",
        )
        st.plotly_chart(fig, width="stretch")

    st.subheader("Ranked prevention-prioritisation table")
    st.dataframe(
        intervention_df,
        width="stretch",
        hide_index=True,
        column_config={
            "area_code": "Area code",
            "area_name": "Area",
            "risk_score": st.column_config.NumberColumn("Demo score", format="%.1f"),
            "risk_tier": "Tier",
            "primary_planning_signal": "Primary planning signal",
            "planning_signal_group": "Signal group",
            "suggested_actions": "Non-clinical workflow prompts",
        },
    )

with area_tab:
    st.subheader(f"Area profile: {selected_area}")
    profile_cols = st.columns(4)
    profile_cols[0].metric("Demo risk score", f"{area_row['risk_score']:.1f}")
    profile_cols[1].metric("Risk tier", area_row["risk_tier"])
    profile_cols[2].metric("NSAID mean / 1,000", f"{area_row['nsaid_mean_items_per_1000']:.1f}")
    profile_cols[3].metric(
        "Cardiometabolic RX density", f"{area_row['cardiometabolic_rx_density']:.1f}"
    )
    st.info(
        f"Primary planning signal: **{area_row['primary_planning_signal']}**. "
        "This is the largest weighted aggregate score component, not a diagnosis, "
        "disease-reporting claim or individual recommendation."
    )

    fig = px.line(
        area_rx,
        x="month",
        y="items_per_1000",
        color="medication_class",
        markers=True,
        labels={"items_per_1000": "Items per 1,000 population", "month": "Month"},
        title=f"Synthetic medication-class trend: {selected_area}",
    )
    st.plotly_chart(fig, width="stretch")

    left_panel, right_panel = st.columns([1, 1])
    with left_panel:
        st.subheader("Score component breakdown")
        breakdown_df = score_component_breakdown(area_row)
        st.dataframe(
            breakdown_df,
            width="stretch",
            hide_index=True,
            column_config={
                "component": "Component",
                "input_value": st.column_config.NumberColumn("Input", format="%.2f"),
                "scaled_signal": st.column_config.NumberColumn("Scaled", format="%.3f"),
                "weight_pct": st.column_config.NumberColumn("Weight %", format="%.1f"),
                "score_contribution": st.column_config.NumberColumn(
                    "Score contribution", format="%.1f"
                ),
                "interpretation": "Interpretation",
            },
        )
        st.subheader("Public-health indicator snapshot")
        st.caption(
            "Synthetic aggregate estimates for planning context only. These are not "
            "reported disease counts or patient-level risk estimates."
        )
        st.dataframe(
            public_health_indicator_snapshot(area_public_health),
            width="stretch",
            hide_index=True,
            column_config={
                "indicator": "Indicator",
                "synthetic_aggregate_value": st.column_config.NumberColumn(
                    "Synthetic aggregate value", format="%.1f"
                ),
                "safe_interpretation": "Safe interpretation",
            },
        )

    with right_panel:
        st.subheader("Regional report generator")
        selected_actions = intervention_df[intervention_df["area_name"] == selected_area][
            "suggested_actions"
        ].iloc[0]
        selected_action_list = [action.strip() for action in selected_actions.split(" | ")]
        st.info(
            "The generated report is non-clinical and intended for aggregate public-health "
            "planning and portfolio demonstration only."
        )
        st.markdown("**Suggested awareness/intervention categories**")
        for action in selected_action_list:
            st.markdown(f"- {action}")

        report_markdown = format_area_report_markdown(
            area_row,
            selected_action_list,
            prescribing_indicators=area_prescribing_summary,
            public_health_indicators=area_public_health,
        )
        report_name = selected_area.lower().replace(" ", "_").replace("-", "_")
        st.download_button(
            "Download regional Markdown report",
            data=report_markdown,
            file_name=f"{report_name}_regional_public_health_report.md",
            mime="text/markdown",
            width="stretch",
        )
        with st.expander("Preview Markdown report"):
            st.markdown(report_markdown)

with method_tab:
    st.subheader("Transparent scoring method")
    st.write(
        "The score is an illustrative composite of min-max scaled area-level signals. "
        "Weights are deliberately visible and simple because this is a prevention-planning "
        "demo, not a black-box clinical prediction model."
    )
    st.markdown(
        """
- NSAID persistence signal: 35%
- Cardiometabolic prescribing density: 25%
- Saturated-fat proxy index: 20%
- Deprivation index: 10%
- Obesity prevalence estimate: 10%
"""
    )
    st.subheader("Governance assumptions")
    st.markdown(
        """
- Synthetic aggregate data is the default data source.
- Real-world use would require documented aggregate data provenance, validation and bias review.
- Outputs are designed for population-level awareness and service-planning discussions.
- The system must not be used for individual triage, diagnosis, treatment, dosing or prescribing.
"""
    )
