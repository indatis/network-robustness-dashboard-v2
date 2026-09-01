from pathlib import Path

import pandas as pd
import streamlit as st

from app.data_loader import filter_dataframe
from app.components import (
    show_asset,
    visual_filters,
    selected_asset,
    show_table,
    download_dataframe,
)


def page_overview(data, visual_index):
    st.header("Experiment overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modularity configurations", "7")
    c2.metric("Realizations per configuration", "40")
    c3.metric("Matched LFR–NULL pairs", "280")
    c4.metric("Primary outcome", "Weighted assortativity")

    st.markdown(
        """
        The experiment compares **weighted-directed LFR networks** with matched
        **degree-preserving NULL networks** under diffuse and targeted attacks.

        Primary robustness is summarized by:
        """
    )

    st.latex(r"\mathrm{AUC}_{|\Delta|} = \int |Y(x)-Y(0)|\,dx")

    st.markdown("For paired LFR–NULL comparisons:")

    st.latex(r"\Delta \mathrm{AUC} = \mathrm{AUC}_{LFR} - \mathrm{AUC}_{NULL}")

    st.markdown(
        """
        **Negative ΔAUC** indicates relatively greater LFR robustness, whereas
        **positive ΔAUC** indicates relatively greater disruption in LFR.
        """
    )

    st.subheader("Power analysis and number of realizations")

    st.markdown(
        """
        The choice of **40 independent realizations per modularity configuration**
        was informed by prospective power analysis conducted before the final
        simulation experiment.

        For the principal matched LFR–NULL comparison, an a priori
        **two-sided paired-samples t test** assuming a medium standardized paired
        effect **dᶻ = 0.50**, significance level **α = 0.05**, and statistical
        power **1 − β = 0.80** required **34 matched pairs**.

        As an additional planning check for analyses involving the seven
        modularity levels, a seven-level repeated-measures calculation assuming
        a medium effect **f = 0.25**, **α = 0.05**, power **= 0.80**, and
        nonsphericity correction **ε = 0.75** returned a requirement of
        **39 observations**.

        The final design therefore used **40 realizations for each of the seven
        modularity configurations**, yielding **280 matched LFR–NULL pairs** in
        total.
        """
    )

    with st.expander("Power-analysis parameters"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
                **Matched LFR–NULL comparison**

                - Test: paired-samples t test
                - Tails: two-sided
                - Effect size: **dᶻ = 0.50**
                - α = **0.05**
                - Power = **0.80**
                - Required matched pairs: **34**
                - Final realizations per configuration: **40**
                """
            )

        with col2:
            st.markdown(
                """
                **Seven-level planning calculation**

                - Test: repeated-measures ANOVA, within factors
                - Effect size: **f = 0.25**
                - α = **0.05**
                - Power = **0.80**
                - Measurements: **7**
                - Nonsphericity correction: **ε = 0.75**
                - Required observations: **39**
                """
            )

        st.caption(
            "The final across-modularity inferential analysis treats modularity "
            "configurations as independent groups. The seven-level calculation "
            "is therefore reported as an a priori simulation-planning check rather "
            "than as the formal power calculation for the final one-way ANOVA."
        )

        st.markdown("#### G*Power outputs")

        img1, img2 = st.columns(2)

        with img1:
            st.image(
                "visuals/08_power_analysis/gpower_paired_ttest.png",
                caption=(
                    "Paired-samples t test: dᶻ = 0.50, α = 0.05, "
                    "power = 0.80 → required N = 34."
                ),
                use_container_width=True,
            )

        with img2:
            st.image(
                "visuals/08_power_analysis/gpower_repeated_measures.png",
                caption=(
                    "Seven-level planning calculation: f = 0.25, α = 0.05, "
                    "power = 0.80, ε = 0.75 → required N = 39."
                ),
                use_container_width=True,
            )

    mod = data.get("modularity_summary")
    if mod is not None and not mod.empty:
        st.subheader("Realized modularity information")
        show_table(mod, height=280)

    if visual_index is not None and not visual_index.empty:
        st.subheader("Visual library")
        counts = (
            visual_index
            .groupby(["visual_family", "extension"])
            .size()
            .reset_index(name="files")
        )
        show_table(counts, height=260)


def page_results_explorer(data, visual_index):
    st.header("Results explorer")
    st.caption(
        "Descriptive trajectory figures: raw levels, signed changes and dashboard summaries."
    )

    if visual_index is None or visual_index.empty:
        st.error("No visual assets found.")
        return

    label = st.radio(
        "Figure family",
        ["Raw + signed-change comparison", "Dashboard panels"],
        horizontal=True,
    )

    family = "luisa" if label.startswith("Raw") else "dashboard"

    work = visual_index[
        visual_index["visual_family"] == family
    ].copy()

    work, selection = visual_filters(work, "explorer")
    row = selected_asset(work, "explorer_figure")

    if row is None:
        st.warning("No figure matches that combination.")
        return

    show_asset(row["path"])


def page_paired_tests(data, visual_index):
    st.header("LFR vs NULL robustness")
    st.caption(
        "Paired ΔAUC is evaluated within each modularity configuration. "
        "ΔAUC < 0: LFR more robust; ΔAUC > 0: LFR more disrupted."
    )

    work = visual_index[
        visual_index["visual_family"] == "paired_delta_auc"
    ].copy()

    work, selection = visual_filters(work, "paired")
    row = selected_asset(work, "paired_figure")

    if row is None:
        st.warning("No paired ΔAUC figure matches that combination.")
        return

    show_asset(row["path"])

    stats = data.get("paired_tests_rebuilt")
    if stats is None or stats.empty:
        stats = data.get("paired_tests")

    filtered = filter_dataframe(
        stats,
        {
            "outcome": selection["outcome"],
            "attack_family": selection["attack_family"],
            "ranking_metric": selection["ranking_metric"],
        },
    )

    st.subheader("Paired-test results")

    preferred = [
        "modularity_regime", "mu_t_input", "Qw",
        "mean_delta_auc", "delta_auc", "mean_paired_delta",
        "ci_low", "ci_high", "ci95_low", "ci95_high",
        "t_stat", "t_statistic", "df",
        "p_value", "p_raw", "p_holm", "p_value_holm",
        "cohen_dz", "n_pairs", "n",
    ]

    show_table(filtered, preferred, 360)
    download_dataframe(filtered, "paired_test_selection.csv")


def page_modularity(data, visual_index):
    st.header("Modularity effects")
    st.caption(
        "Across-modularity ANOVA/Welch analyses are performed separately for "
        "LFR and NULL. Post-hoc tests identify which configurations differ."
    )

    work = visual_index[
        visual_index["visual_family"] == "anova"
    ].copy()

    work, selection = visual_filters(work, "anova")
    row = selected_asset(work, "anova_figure")

    if row is None:
        st.warning("No ANOVA figure matches that combination.")
        return

    show_asset(row["path"])

    filters = {
        "outcome": selection["outcome"],
        "attack_family": selection["attack_family"],
        "ranking_metric": selection["ranking_metric"],
    }

    st.subheader("Omnibus results")
    anova = filter_dataframe(data.get("anova_all"), filters)
    show_table(anova, height=300)

    with st.expander("Post-hoc comparisons"):
        t1, t2 = st.tabs(["Tukey HSD", "Games–Howell"])

        with t1:
            tukey = filter_dataframe(data.get("tukey_all"), filters)
            show_table(tukey, height=350)
            download_dataframe(tukey, "tukey_selection.csv")

        with t2:
            gh = filter_dataframe(data.get("games_howell_all"), filters)
            show_table(gh, height=350)
            download_dataframe(gh, "games_howell_selection.csv")


def page_animations(data, visual_index):
    st.header("Attack animations")
    st.caption(
        "Illustrative mechanism examples from one representative strong-community "
        "pair. Inferential conclusions use all 40 realizations."
    )

    choice = st.radio(
        "Third panel",
        [
            "Raw weighted-directed community assortativity Y(x)",
            "Absolute disruption |Y(x) − Y(0)|",
        ],
        horizontal=True,
    )

    family = "gif_raw_y" if choice.startswith("Raw") else "gif_disruption"

    work = visual_index[
        (visual_index["visual_family"] == family)
        & (visual_index["extension"] == ".gif")
    ].copy()

    if work.empty:
        st.warning("No GIFs found.")
        return

    idx = st.selectbox(
        "Attack example",
        list(work.index),
        format_func=lambda i: work.loc[i, "display_name"],
    )

    show_asset(work.loc[idx, "path"])

    st.caption(
        "The first two panels show the perturbed LFR network and its matched "
        "degree-preserving NULL. The third panel tracks the primary community-"
        "assortativity outcome for the same illustrative network pair."
    )


def page_heatmaps(data, visual_index):
    st.header("Summary heatmaps")

    work = visual_index[
        visual_index["visual_family"] == "heatmap"
    ].copy()

    if work.empty:
        st.warning("No heatmaps found.")
        return

    idx = st.selectbox(
        "Heatmap",
        list(work.index),
        format_func=lambda i: work.loc[i, "display_name"],
    )

    show_asset(work.loc[idx, "path"])


def page_downloads(data, visual_index):
    st.header("Compact data downloads")
    st.caption(
        "Download the compact result tables used by the dashboard. "
        "Large raw simulation files are intentionally excluded."
    )

    options = [
        key for key, value in data.items()
        if (
            not key.endswith("_path")
            and isinstance(value, pd.DataFrame)
            and not value.empty
        )
    ]

    if not options:
        st.info("No compact tables found.")
        return

    selected = st.selectbox(
        "Table",
        sorted(options),
        format_func=lambda x: x.replace("_", " ").title(),
    )

    df = data[selected]
    show_table(df, height=420)
    download_dataframe(
        df,
        f"{selected}.csv",
        "Download selected table",
    )
