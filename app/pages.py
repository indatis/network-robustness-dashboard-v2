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


# ============================================================
# SMALL EXPLANATION HELPERS
# ============================================================

def _overview_glossary():
    with st.expander("Statistical glossary / meeting cheat sheet"):
        st.markdown(
            """
            **AUC of absolute change**  
            One number summarizing the total amount of departure from the
            network's own pre-attack baseline across the whole attack path.
            **Smaller AUC = more robust. Larger AUC = more disrupted.**

            **Why absolute change?**  
            Robustness here means *how far* the network moves from baseline,
            regardless of whether the outcome moves upward or downward.
            Direction is retained separately in the **signed-change** and
            **raw-trajectory** figures.

            **Paired ΔAUC**  
            `ΔAUC = AUC_LFR − AUC_NULL`.

            - `ΔAUC < 0` → LFR is more robust than its matched NULL.
            - `ΔAUC > 0` → LFR is more disrupted than its matched NULL.
            - `ΔAUC ≈ 0` → similar robustness.

            **Paired t-test**  
            Tests whether the mean paired ΔAUC differs from zero. LFR and NULL
            are intentionally dependent **within each matched pair**. The
            independent inferential units are the matched network-realization
            pairs, not the individual attack steps.

            **Holm correction**  
            Controls family-wise error when the same inferential question is
            tested across multiple modularity regimes. **Holm addresses multiple
            testing, not dependence.**

            **Cohen dᶻ**  
            Standardized effect size for the paired LFR–NULL difference. Its sign
            follows ΔAUC; its magnitude describes how strong the paired effect is
            relative to the variability of the paired differences.

            **One-way ANOVA**  
            Tests whether mean AUC differs somewhere across the seven modularity
            regimes within LFR or within NULL.

            **Welch ANOVA**  
            Answers the same omnibus question but is more robust when group
            variances are unequal.

            **ω² (omega squared)**  
            Effect size for the across-modularity analysis. Larger values mean
            that robustness depends more strongly on modularity regime.

            **Tukey HSD / Games–Howell**  
            Post-hoc tests used after the omnibus analysis to identify which
            specific modularity regimes differ. Games–Howell is preferable when
            equal-variance assumptions are not supported.

            **Planted communities vs dynamic Louvain**  
            The planted-community outcome uses the known LFR ground-truth
            partition. Dynamic Louvain re-estimates communities after
            perturbation and is best interpreted as a secondary/sensitivity
            view of the community structure.
            """
        )


def _paired_tests_guide():
    with st.expander("How to read this page / Why the paired test is used"):
        st.markdown(
            """
            ### What is being compared?

            At each modularity regime, every LFR realization has its own matched
            degree-preserving NULL. The whole perturbation trajectory of each
            network is first summarized into **one AUC value**.

            For each matched pair:
            """
        )

        st.latex(
            r"\Delta \mathrm{AUC}"
            r" = "
            r"\mathrm{AUC}_{LFR}"
            r" - "
            r"\mathrm{AUC}_{NULL}"
        )

        st.markdown(
            """
            ### How to read the paired ΔAUC plot

            - **Zero line** → LFR and NULL have equal average disruption.
            - **Point above zero** → LFR has larger AUC → LFR is less robust.
            - **Point below zero** → LFR has smaller AUC → LFR is more robust.
            - **Each plotted point** summarizes the mean of the 40 matched
              LFR–NULL ΔAUC values at that modularity regime.
            - **Error bar** shows uncertainty around that mean.
            - **Stars** indicate statistical significance after the relevant
              multiple-testing adjustment.

            ### Why a paired t-test?

            The LFR and NULL observations are **not supposed to be independent
            within a pair**: each NULL was constructed as the matched control for
            one specific LFR realization. The paired t-test uses the 40
            within-pair differences and asks whether their mean is zero.

            The important independence assumption is **between matched pairs**:
            realization pair 1 should be independent of realization pair 2, and
            so on.

            The individual attack steps are also not treated as independent
            observations. They are compressed into one AUC per realization
            before inference, avoiding pseudo-replication.

            ### Why Holm correction?

            The paired LFR–NULL comparison is repeated across the seven
            modularity regimes. Repeating tests increases the chance of a false
            positive. Holm correction controls the family-wise error rate across
            that family of tests.

            **Important:** Holm correction addresses **multiple testing**, not
            the dependence between LFR and NULL. Dependence within a matched pair
            is handled by the paired design.

            ### What does Cohen dᶻ add?

            The p-value answers: **Is there evidence of an LFR–NULL difference?**

            Cohen dᶻ answers: **How large is that paired difference relative to
            its variability?**

            The sign follows ΔAUC:

            - negative dᶻ → effect favors LFR robustness;
            - positive dᶻ → LFR is more disrupted.
            """
        )


def _modularity_guide():
    with st.expander("How to read the boxplots / ANOVA / post-hoc tests"):
        st.markdown(
            """
            ### What question does this page answer?

            This page does **not** primarily compare LFR against NULL. Instead it
            asks, separately within LFR and within NULL:

            **Does robustness change across the seven modularity regimes?**

            The robustness variable being compared is the AUC of the absolute
            departure from baseline. **Lower AUC = more robust. Higher AUC =
            more disrupted.**

            ### What is each point in a boxplot?

            Each modularity regime contains **40 independently generated network
            realizations**.

            - **One colored dot** = the AUC from one network realization.
            - **Box** = middle 50% of those AUC values.
            - **Line inside the box** = median.
            - **Green triangle** = mean.
            - **Whiskers** = conventional non-outlying range.
            - **Isolated circles** = conventional boxplot outliers.

            Therefore ANOVA is performed on the realization-level AUC values,
            not merely on the seven boxplot means.

            ### What does the omnibus ANOVA test?

            The null hypothesis is that the seven modularity groups have the same
            mean AUC.
            """
        )

        st.latex(
            r"H_0:\ "
            r"\mu_{AUC,1}"
            r"="
            r"\mu_{AUC,2}"
            r"="
            r"\cdots"
            r"="
            r"\mu_{AUC,7}"
        )

        st.markdown(
            """
            - **Small p-value** → evidence that at least one modularity regime
              differs.
            - The omnibus p-value **does not tell us which groups differ**.
            - A significant ANOVA **does not imply a monotonic trend**. Always
              inspect the shape of the boxes/means across modularity.

            ### Why also report Welch ANOVA?

            Classical one-way ANOVA is most natural when group variances are
            reasonably similar. Welch ANOVA is more robust to unequal variances.
            Agreement between ANOVA and Welch makes the conclusion less dependent
            on the equal-variance assumption.

            ### What is ω²?

            **Omega squared (ω²)** measures the size of the modularity effect.
            Larger values mean that the AUC distributions depend more strongly
            on modularity regime.

            The p-value answers **whether evidence of a difference exists**;
            ω² answers **how important the modularity grouping is**.

            ### Where are Tukey and Games–Howell in the visual?

            The horizontal significance brackets above the boxplots are the
            displayed post-hoc comparisons.

            - `*` → adjusted p < .05
            - `**` → adjusted p < .01
            - `***` → adjusted p < .001

            Tukey HSD evaluates pairwise differences under the standard
            equal-variance framework. Games–Howell is the more robust post-hoc
            option when variances differ.

            The figure may display only significant comparisons against a chosen
            reference regime (for readability), even though the underlying
            post-hoc table contains the full set of pairwise comparisons.

            **The reference regime is a visualization choice, not a requirement
            of Tukey itself.**

            ### LFR panel vs NULL panel

            The ANOVA is run **separately** for LFR and NULL.

            - LFR panel → does LFR robustness vary across modularity?
            - NULL panel → do the matched control networks show a corresponding
              regime-dependent pattern?

            A large LFR ω² together with a near-zero NULL ω² is evidence that the
            across-modularity pattern is tied to the organized LFR architecture
            rather than simply to the matched degree/weight constraints.
            """
        )


def _results_explorer_guide(label):
    if label.startswith("Raw"):
        with st.expander("How to read Raw + signed-change figures"):
            st.markdown(
                """
                These figures are **descriptive/mechanistic** views of the
                perturbation trajectories. They help explain *how* the network
                moves during an attack.

                ### Raw trajectory

                The raw panel shows the actual value of the network outcome
                `Y(x)` as attack intensity `x` increases.

                Use it to answer:

                - What was the starting value?
                - Does the metric rise or fall?
                - Is the response gradual, abrupt, monotonic, or non-monotonic?
                - Do LFR and NULL follow different trajectories?

                ### Signed change

                The signed-change panel shows:
                """
            )

            st.latex(r"Y(x)-Y(0)")

            st.markdown(
                """
                - negative value → the outcome decreased from baseline;
                - positive value → the outcome increased from baseline;
                - zero → no change from baseline.

                This view preserves the **direction** of change.

                ### Why do we still use absolute AUC for inference?

                The robustness statistic asks **how far the network moves from
                its own baseline**, regardless of direction. Therefore the AUC is
                built from the absolute deviation:
                """
            )

            st.latex(r"|Y(x)-Y(0)|")

            st.markdown(
                """
                So the two views are complementary:

                - **absolute AUC** → magnitude of disruption / robustness;
                - **signed trajectory** → direction and mechanism of the change.

                AUC does not replace the raw/signed figures; it summarizes them
                into one realization-level robustness number for statistical
                testing.
                """
            )

    else:
        with st.expander("How to read Dashboard panels"):
            st.markdown(
                """
                Dashboard panels provide a compact overview across attacks,
                modularity regimes, rankings, and graph types.

                Depending on the selected view, the plotted quantity is:

                **Raw**
                """
            )

            st.latex(r"Y(x)")

            st.markdown(
                """
                The actual network metric at each attack intensity.

                **Signed delta**
                """
            )

            st.latex(r"Y(x)-Y(0)")

            st.markdown(
                """
                Shows direction relative to baseline:

                - negative → metric decreased;
                - positive → metric increased.

                **Absolute delta**
                """
            )

            st.latex(r"|Y(x)-Y(0)|")

            st.markdown(
                """
                Shows the magnitude of departure from baseline without direction.
                This absolute-deviation trajectory is what is integrated to
                obtain the AUC robustness statistic.

                ### Practical reading order

                1. Use **Raw** to understand the actual outcome level.
                2. Use **Signed delta** to understand direction.
                3. Use **Absolute delta** to compare disruption magnitude.
                4. Use the paired-test and ANOVA pages for formal inference.
                """
            )


def _heatmap_guide(display_name):
    name = str(display_name).lower()

    with st.expander("How to read this heatmap", expanded=True):
        if "omega2" in name or "omega" in name:
            if "lfr" in name:
                network_label = "LFR"
            elif "null" in name:
                network_label = "NULL"
            else:
                network_label = "selected network type"

            st.markdown(
                f"""
                ### Across-modularity effect-size heatmap ({network_label})

                This heatmap summarizes the **ANOVA across modularity regimes**.

                - **Rows** = network outcomes.
                - **Columns** = attack strategy + ranking/subset criterion.
                - **Number in each cell** = omega squared (ω²), the ANOVA effect size.
                - **Larger ω²** = robustness depends more strongly on modularity.
                - **ω² near zero** = little dependence on modularity.
                - **Color intensity** is another visual encoding of the same effect size.
                - **Stars** indicate the significance level of the corresponding
                  omnibus across-modularity test.

                The p-value and ω² answer different questions:

                - **p-value** → is there evidence that at least one modularity
                  regime differs?
                - **ω²** → how strong is the modularity effect?

                For the pre-specified planted weighted-directed assortativity
                family, significance markings use the Holm-adjusted primary
                omnibus results. Other outcome families are exploratory unless
                otherwise stated.

                Use this heatmap to identify interesting cells, then open the
                corresponding **Modularity effects** boxplot to see the actual
                shape of the seven AUC distributions and the post-hoc contrasts.
                """
            )

            if "null" in name:
                st.info(
                    "Important: the modularity labels on the NULL side refer to "
                    "the LFR regimes from which the matched NULL controls were "
                    "constructed. They do not mean that the NULL networks "
                    "themselves retain the same planted modularity."
                )

        elif "mean delta auc" in name or "mean_delta_auc" in name:
            st.markdown(
                """
                ### Paired LFR–NULL difference heatmap

                This heatmap summarizes the **mean paired ΔAUC**:
                """
            )

            st.latex(
                r"\Delta \mathrm{AUC}"
                r" = "
                r"\mathrm{AUC}_{LFR}"
                r" - "
                r"\mathrm{AUC}_{NULL}"
            )

            st.markdown(
                """
                Read the sign first:

                - **negative ΔAUC** → LFR has smaller disruption → LFR more robust;
                - **positive ΔAUC** → LFR has larger disruption → LFR less robust;
                - **near zero** → LFR and NULL have similar robustness.

                The magnitude tells you how large the LFR–NULL difference is in
                the original AUC units.

                Use this heatmap as a summary/screening tool. Then open the
                corresponding **LFR vs NULL robustness** plot to see the paired
                estimate, uncertainty, Holm-adjusted significance, and detailed
                table.
                """
            )

        elif "cohen" in name or "dz" in name:
            st.markdown(
                """
                ### Standardized paired-effect heatmap

                This heatmap summarizes **Cohen dᶻ** from the paired LFR–NULL
                comparisons.

                - **negative dᶻ** → effect favors LFR robustness;
                - **positive dᶻ** → LFR is more disrupted;
                - **larger |dᶻ|** → stronger paired effect relative to the
                  variability of the paired differences.

                Unlike mean ΔAUC, dᶻ is standardized. This makes it useful for
                comparing effect strength across different outcomes or attack
                strategies that may have different numerical scales.

                Use the corresponding **LFR vs NULL robustness** page for the
                unstandardized ΔAUC, confidence interval, p-value, and Holm
                adjustment.
                """
            )

        else:
            st.markdown(
                """
                This heatmap is a compact summary across outcomes and attack
                configurations. Read the row and column labels to identify the
                outcome × attack combination, then use the detailed paired-test
                or modularity-effects page for the full inferential result.

                Heatmaps are best used to answer **“Where should I look?”**
                rather than as a replacement for the detailed plots.
                """
            )


# ============================================================
# OVERVIEW
# ============================================================

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

    st.markdown(
        """
        Think of this AUC as **total accumulated disruption across the whole
        attack**. A smaller value means that the network remained closer to its
        own pre-attack state.
        """
    )

    st.markdown("For paired LFR–NULL comparisons:")

    st.latex(r"\Delta \mathrm{AUC} = \mathrm{AUC}_{LFR} - \mathrm{AUC}_{NULL}")

    st.markdown(
        """
        **Negative ΔAUC** indicates relatively greater LFR robustness, whereas
        **positive ΔAUC** indicates relatively greater disruption in LFR.
        """
    )

    _overview_glossary()

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


# ============================================================
# RESULTS EXPLORER
# ============================================================

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

    _results_explorer_guide(label)

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


# ============================================================
# PAIRED LFR vs NULL TESTS
# ============================================================

def page_paired_tests(data, visual_index):
    st.header("LFR vs NULL robustness")
    st.caption(
        "Paired ΔAUC is evaluated within each modularity configuration. "
        "ΔAUC < 0: LFR more robust; ΔAUC > 0: LFR more disrupted."
    )

    _paired_tests_guide()

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


# ============================================================
# MODULARITY EFFECTS
# ============================================================

def page_modularity(data, visual_index):
    st.header("Modularity effects")
    st.caption(
        "Across-modularity ANOVA/Welch analyses are performed separately for "
        "LFR and NULL. Post-hoc tests identify which configurations differ."
    )

    _modularity_guide()

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
        st.caption(
            "The omnibus test says whether any modularity groups differ. "
            "These tables identify the specific pairwise differences."
        )

        t1, t2 = st.tabs(["Tukey HSD", "Games–Howell"])

        with t1:
            tukey = filter_dataframe(data.get("tukey_all"), filters)
            show_table(tukey, height=350)
            download_dataframe(tukey, "tukey_selection.csv")

        with t2:
            gh = filter_dataframe(data.get("games_howell_all"), filters)
            show_table(gh, height=350)
            download_dataframe(gh, "games_howell_selection.csv")


# ============================================================
# ATTACK ANIMATIONS
# ============================================================

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

    with st.expander("How to read the animation"):
        if choice.startswith("Raw"):
            st.markdown(
                """
                The first two panels show how the representative LFR and matched
                NULL networks change during the attack. The third panel shows
                the **actual weighted-directed community assortativity Y(x)**.

                This version is useful for understanding the **direction and
                mechanism** of the response. It is illustrative only; formal
                inference uses all 40 realizations per modularity regime.
                """
            )
        else:
            st.markdown(
                """
                The first two panels show how the representative LFR and matched
                NULL networks change during the attack. The third panel shows the
                **absolute departure from baseline |Y(x) − Y(0)|**.

                Larger values mean greater structural departure from the
                pre-attack state. The area accumulated under this disruption
                trajectory is the AUC robustness statistic. This animation is
                illustrative only; formal inference uses all 40 realizations.
                """
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


# ============================================================
# HEATMAPS
# ============================================================

def page_heatmaps(data, visual_index):
    st.header("Summary heatmaps")
    st.caption(
        "Heatmaps summarize many outcome × attack combinations at once. "
        "Use them to identify patterns, then inspect the corresponding detailed plot."
    )

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

    selected_name = work.loc[idx, "display_name"]
    _heatmap_guide(selected_name)

    show_asset(work.loc[idx, "path"])


# ============================================================
# DOWNLOADS
# ============================================================

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
