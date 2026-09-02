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
# OPTIONAL METHODS-PAGE VISUAL ASSETS
# ============================================================

METHOD_ASSETS_DIR = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "methods"
)


def _show_method_asset(filename, caption=None):
    """
    Show an optional explanatory asset used by the Methods & metrics page.

    Assets live outside visuals/ so they are not mixed into the generated
    scientific-figure index used by the Results/Heatmap pages.
    """
    path = METHOD_ASSETS_DIR / filename

    if not path.exists():
        st.info(
            f"Optional methods visual not found yet: "
            f"`assets/methods/{filename}`"
        )
        return

    show_asset(path, caption=caption)


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
# METHODS & METRIC GUIDE
# ============================================================

def page_methods(data, visual_index):
    st.header("Methods & metric guide")
    st.caption(
        "A compact reference for the network generator, matched NULL, "
        "outcome variables, attacks, rankings, formulas, and inferential workflow."
    )

    st.info(
        "Primary inferential outcome: **weighted-directed community assortativity "
        "using the planted LFR communities**. Dynamic weighted Louvain is retained "
        "as a secondary/sensitivity view in which the community partition is "
        "allowed to adapt after perturbation."
    )

    # --------------------------------------------------------
    # Visual workflow
    # --------------------------------------------------------
    st.subheader("Analysis workflow")

    step_titles = [
        "1. Generate",
        "2. Match",
        "3. Perturb",
        "4. Measure",
        "5. Summarize",
        "6. Infer",
    ]
    step_text = [
        "Weighted-directed LFR",
        "Degree-preserving NULL",
        "Node / edge attack",
        "Compute Y(x)",
        "Trajectory → AUC",
        "Paired tests + ANOVA",
    ]

    cols = st.columns(6)
    for col, title, body in zip(cols, step_titles, step_text):
        with col:
            st.markdown(
                f"""
                <div style="
                    border:1px solid rgba(128,128,128,0.35);
                    border-radius:10px;
                    padding:12px;
                    min-height:115px;
                    text-align:center;">
                    <b>{title}</b><br><br>
                    <span style="font-size:0.92rem;">{body}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        The workflow answers two complementary questions:

        - **LFR vs NULL:** does the organized LFR architecture make the network
          more or less robust than its matched structural control?
        - **Across modularity:** does robustness change as the strength of the
          LFR community structure changes?
        """
    )

    tab_design, tab_outcomes, tab_attacks, tab_null, tab_software = st.tabs(
        [
            "Experimental design",
            "Outcome variables Y",
            "Attacks & rankings",
            "Matched NULL",
            "Software & references",
        ]
    )

    # ========================================================
    # TAB 1 — EXPERIMENTAL DESIGN
    # ========================================================
    with tab_design:
        st.subheader("Network generator and modularity transition")

        st.markdown(
            """
            Networks are generated with the **official weighted-directed LFR C++
            benchmark**. The active experiment uses seven values with
            `μ_t = μ_w`. Smaller mixing values imply stronger planted-community
            structure.
            """
        )

        design_table = pd.DataFrame(
            [
                ["Nodes", "150"],
                ["Average degree", "10"],
                ["Maximum degree", "25"],
                ["Degree exponent τ₁", "2.5"],
                ["Community-size exponent τ₂", "1.5"],
                ["Strength-degree exponent β", "1.5"],
                ["Community size", "20–45 nodes"],
                ["Mixing grid μₜ = μw", "0.075, 0.100, 0.125, 0.150, 0.175, 0.225, 0.300"],
                ["Independent LFR realizations", "40 per modularity configuration"],
                ["Matched LFR–NULL pairs", "280 total"],
                ["Random attack repetitions", "5 within each realization"],
            ],
            columns=["Design element", "Value"],
        )
        show_table(design_table, height=390)

        st.warning(
            "**The 5 random repetitions are not five additional independent "
            "samples.** They repeat stochastic attack orders inside the same "
            "network realization and are averaged before inference. The "
            "independent units are the 40 LFR realizations per modularity "
            "configuration."
        )

        st.markdown("### Mixing parameter versus realized modularity")
        st.latex(r"\mu \downarrow \quad \Longrightarrow \quad Q_w \uparrow")

        st.markdown(
            """
            Thus `μ = 0.075` is the strongest-community regime in the active
            transition and `μ = 0.300` is the weakest. The dashboard often uses
            **realized weighted modularity `Qw`** because it reports the
            community structure actually generated rather than only the input
            parameter.
            """
        )


        st.markdown("### Example edge-weight structure")
        st.markdown(
            """
            Because the experiment is weighted, it is useful to inspect the
            distribution of the LFR edge weights themselves. The left panel
            shows the original edge-weight distribution; the right panel shows
            the same weights after the transformation `log(1 + weight)`.

            This figure is **descriptive**: it illustrates the kind of weighted
            heterogeneity present in one representative LFR realization. It is
            not an inferential result and does not replace the 40-run analysis.
            """
        )

        _show_method_asset(
            "edge_weight_distribution.png",
            caption=(
                "Representative official weighted-directed LFR edge-weight "
                "distribution and log-transformed view."
            ),
        )

        with st.expander("Why do some descriptive dashboard plots show only three rows?"):
            st.markdown(
                """
                Some trajectory panels show three representative regimes for
                readability:

                - **weak:** μ = 0.300, Qw ≈ 0.460
                - **intermediate:** μ = 0.150, Qw ≈ 0.620
                - **strong:** μ = 0.075, Qw ≈ 0.690

                These are descriptive summaries. The paired tests and
                across-modularity ANOVA use **all seven regimes and all 40
                independent realizations per regime**.
                """
            )

    # ========================================================
    # TAB 2 — OUTCOMES
    # ========================================================
    with tab_outcomes:
        st.subheader("Outcome variables Y")
        st.markdown(
            """
            At each perturbation state the notebook computes a set of network
            outcomes, written generically as `Y(x)`. The formulas below are the
            formulas actually implemented in the simulation, followed by an
            explanation of every symbol.
            """
        )

        # ----------------------------------------------------
        # Unweighted community assortativity
        # ----------------------------------------------------
        with st.expander("Unweighted community assortativity"):
            st.markdown(
                """
                **Question:** do directed edges remain preferentially inside the
                same community?

                Define the directed mixing matrix:
                """
            )
            st.latex(
                r"e_{gh}="
                r"\frac{1}{m}"
                r"\sum_{(u,v)\in E}"
                r"\mathbf{1}\{c_u=g,\;c_v=h\}"
            )
            st.latex(
                r"a_g=\sum_h e_{gh},"
                r"\qquad"
                r"b_g=\sum_h e_{hg}"
            )
            st.latex(
                r"r="
                r"\frac{\operatorname{Tr}(e)-\sum_g a_g b_g}"
                r"{1-\sum_g a_g b_g}"
            )

            st.markdown(
                """
                **Components**

                - `m` = number of directed edges.
                - `c_u`, `c_v` = community labels of source `u` and target `v`.
                - `e_gh` = fraction of directed edges from community `g` to
                  community `h`.
                - `a_g` = fraction of edges originating from community `g`.
                - `b_g` = fraction of edges arriving at community `g`.
                - `Tr(e)` = fraction of edges whose source and target are in the
                  same community.
                - `r` = categorical community assortativity.

                **Interpretation**

                - `r > 0` → more within-community edges than expected.
                - `r ≈ 0` → no clear categorical mixing preference.
                - `r < 0` → relatively more between-community edges.

                This version is **unweighted**. Weakening an existing edge
                without deleting it does not change the edge-count mixing matrix.

                **Reference:** Newman, M. E. J. (2003), *Mixing patterns in
                networks*. The notebook evaluates this formula through
                NetworkX's categorical attribute-assortativity implementation.
                """
            )

        # ----------------------------------------------------
        # Weighted directed community assortativity
        # ----------------------------------------------------
        with st.expander(
            "Weighted-directed community assortativity — PRIMARY",
            expanded=True,
        ):
            st.markdown(
                """
                **Question:** does the **total directed edge weight** remain
                preferentially inside communities?

                First construct a weighted community mixing matrix:
                """
            )
            st.latex(
                r"M_{gh}="
                r"\sum_{(u,v)\in E}"
                r"w_{uv}\,"
                r"\mathbf{1}\{c_u=g,\;c_v=h\}"
            )
            st.latex(
                r"W=\sum_{(u,v)\in E}w_{uv},"
                r"\qquad"
                r"e_{gh}=\frac{M_{gh}}{W}"
            )
            st.latex(
                r"a_g=\sum_h e_{gh},"
                r"\qquad"
                r"b_g=\sum_h e_{hg}"
            )
            st.latex(
                r"r_w="
                r"\frac{\operatorname{Tr}(e)-\sum_g a_g b_g}"
                r"{1-\sum_g a_g b_g}"
            )

            st.markdown(
                """
                **Components**

                - `w_uv` = weight of directed edge `u → v`.
                - `M_gh` = total weight flowing from source community `g` to
                  target community `h`.
                - `W` = total positive edge weight in the graph.
                - `e_gh` = normalized fraction of total weight flowing `g → h`.
                - `a_g` = fraction of total weight originating from community
                  `g`.
                - `b_g` = fraction of total weight arriving at community `g`.
                - `Tr(e)` = observed fraction of total weight remaining inside
                  the same community.
                - `r_w` = weighted-directed categorical assortativity.

                **Interpretation**

                - positive → more total weight remains inside communities than
                  expected from the source/target marginals;
                - near zero → little weighted community preference;
                - negative → relatively more weight crosses between communities.

                **Why primary?** It directly combines the three ingredients of
                the experiment: **direction, edge weight, and community
                membership**.

                **Reference:** Newman (2003), *Mixing patterns in networks*.
                The notebook explicitly adapts Newman's categorical
                mixing-matrix formula by replacing edge counts with normalized
                edge-weight flows.
                """
            )

        # ----------------------------------------------------
        # Dynamic Louvain
        # ----------------------------------------------------
        with st.expander("Dynamic weighted-Louvain community outcomes"):
            st.markdown(
                """
                The two dynamic-Louvain outcomes use the **same assortativity
                formulas shown above**, but replace the fixed planted labels
                `c_i` with a partition re-detected on the current perturbed
                graph:
                """
            )
            st.latex(r"c_i \quad \longrightarrow \quad c_i(x)")
            st.markdown(
                """
                where `c_i(x)` is the weighted-Louvain community assigned to node
                `i` at perturbation state `x`.

                Louvain is run **once per graph state**, and that same partition
                is reused for both dynamic community-assortativity outcomes.

                **Interpretation:** planted-community outcomes measure survival
                of the known original benchmark structure; dynamic-Louvain
                outcomes measure the residual/adaptive community organization
                after the graph is allowed to repartition.

                **Reference for the Louvain method:** Blondel, Guillaume,
                Lambiotte & Lefebvre (2008), *Fast unfolding of communities in
                large networks*.
                """
            )

        # ----------------------------------------------------
        # Yuan assortativity
        # ----------------------------------------------------
        with st.expander("Yuan out–in strength assortativity"):
            st.markdown(
                """
                **Question:** do nodes that send a large total weight tend to
                connect to nodes that receive a large total weight?

                For each edge `u → v`, define source out-strength and target
                in-strength:
                """
            )
            st.latex(
                r"s_u^{out}=\sum_j w_{uj},"
                r"\qquad"
                r"s_v^{in}=\sum_i w_{iv}"
            )
            st.markdown("For the edge-level weighted correlation:")
            st.latex(
                r"x_{uv}=s_u^{out},"
                r"\qquad"
                r"y_{uv}=s_v^{in},"
                r"\qquad"
                r"W=\sum_{(u,v)\in E}w_{uv}"
            )
            st.latex(
                r"\bar{x}="
                r"\frac{\sum_{(u,v)}w_{uv}x_{uv}}{W},"
                r"\qquad"
                r"\bar{y}="
                r"\frac{\sum_{(u,v)}w_{uv}y_{uv}}{W}"
            )
            st.latex(
                r"\sigma_x="
                r"\sqrt{\frac{\sum_{(u,v)}w_{uv}(x_{uv}-\bar{x})^2}{W}},"
                r"\qquad"
                r"\sigma_y="
                r"\sqrt{\frac{\sum_{(u,v)}w_{uv}(y_{uv}-\bar{y})^2}{W}}"
            )
            st.latex(
                r"\rho_{out,in}="
                r"\frac{\sum_{(u,v)}"
                r"w_{uv}(x_{uv}-\bar{x})(y_{uv}-\bar{y})}"
                r"{W\,\sigma_x\sigma_y}"
            )

            st.markdown(
                """
                **Components**

                - `s_u^out` = total weight sent by source node `u`.
                - `s_v^in` = total weight received by target node `v`.
                - `x_uv`, `y_uv` = source and target strength features attached
                  to edge `u → v`.
                - `w_uv` = weight of that edge and therefore the observation
                  weight in the correlation.
                - `W` = total edge weight.
                - `x̄`, `ȳ` = weighted means.
                - `σ_x`, `σ_y` = weighted standard deviations.
                - `ρ_out,in` = weighted Pearson correlation.

                **Interpretation**

                - positive → strong senders tend to connect to strong receivers;
                - near zero → little linear strength association;
                - negative → strong senders tend to connect to weaker receivers,
                  or vice versa.

                **Reference:** Yuan, Y., Yan, J. & Zhang, P. (2021),
                *Assortativity Measures for Weighted and Directed Networks*,
                Section 2, Equations (1)–(2). The notebook notes that the Python
                implementation was checked against the corresponding `wdnet`
                implementation.
                """
            )

        # ----------------------------------------------------
        # GSCC
        # ----------------------------------------------------
        with st.expander("GSCC ratio"):
            st.markdown(
                """
                **GSCC = Giant Strongly Connected Component.**

                Let `C_max(G_x)` be the largest strongly connected component of
                the current graph and `n₀` the number of nodes in the original
                unperturbed graph:
                """
            )
            st.latex(
                r"\mathrm{GSCC}(x)="
                r"\frac{|C_{\max}(G_x)|}{n_0}"
            )
            st.markdown(
                """
                **Components**

                - `G_x` = graph after attack intensity `x`.
                - `C_max(G_x)` = largest set in which every node can reach every
                  other node following directed paths.
                - `n₀` = original number of nodes, kept fixed across the attack.

                **Interpretation:** 1 means the full original node set remains in
                one mutually reachable directed core; values approaching zero
                indicate directed fragmentation.

                **Implementation note:** computed with NetworkX strongly
                connected components. The simulation notebook does not cite a
                separate methodological paper for this diagnostic.
                """
            )

        # ----------------------------------------------------
        # Reachability
        # ----------------------------------------------------
        with st.expander("Directed reachability ratio"):
            st.markdown(
                """
                For every ordered pair of distinct original nodes, define an
                indicator equal to 1 if a directed path currently exists:
                """
            )
            st.latex(
                r"R(x)="
                r"\frac{1}{n_0(n_0-1)}"
                r"\sum_{u\ne v}"
                r"\mathbf{1}\{u\rightsquigarrow v\text{ in }G_x\}"
            )
            st.markdown(
                """
                **Components**

                - `u ↝ v` = at least one directed path from `u` to `v`.
                - `n₀(n₀−1)` = all possible ordered source-target pairs in the
                  original network.
                - removed or unreachable nodes/pairs contribute zero.

                **Interpretation:** 1 means every original ordered pair remains
                reachable; 0.5 means half remain reachable.

                **Implementation note:** path existence is evaluated through
                NetworkX directed reachability. No separate methodological paper
                is cited in the notebook for this diagnostic.
                """
            )

        # ----------------------------------------------------
        # Weighted efficiency
        # ----------------------------------------------------
        with st.expander("Directed weighted global efficiency"):
            st.markdown(
                """
                Edge weight is first converted to an effective path cost:
                """
            )
            st.latex(r"\ell_{uv}=\frac{1}{w_{uv}}")
            st.markdown(
                """
                Let `d_x(u,v)` be the shortest directed path length computed from
                those costs. Then:
                """
            )
            st.latex(
                r"E_w(x)="
                r"\frac{1}{n_0(n_0-1)}"
                r"\sum_{\substack{u\ne v\\u\rightsquigarrow v}}"
                r"\frac{1}{d_x(u,v)}"
            )
            st.markdown(
                """
                **Components**

                - `w_uv` = edge strength.
                - `ℓ_uv = 1/w_uv` = effective edge distance; stronger edges are
                  shorter.
                - `d_x(u,v)` = shortest weighted directed path from `u` to `v`
                  at attack state `x`.
                - unreachable pairs contribute zero.
                - `n₀(n₀−1)` remains fixed at the original network size.

                **Interpretation:** larger values mean short/strong directed
                communication paths remain available; smaller values indicate
                weaker, longer, lost, or unreachable routes.

                Because `d_x(u,v)` can be smaller than 1, this weighted
                efficiency is not necessarily bounded above by 1.

                **Implementation note:** the notebook uses NetworkX all-pairs
                Dijkstra shortest-path lengths. No separate methodological paper
                is cited there for this diagnostic.
                """
            )

        # ----------------------------------------------------
        # Kappa
        # ----------------------------------------------------
        with st.expander("Spectral κ — generalized algebraic connectivity"):
            st.markdown(
                """
                The notebook uses the directed weighted Laplacian:
                """
            )
            st.latex(r"L=D-A")
            st.markdown(
                """
                It then finds the positive normalized left zero-eigenvector:
                """
            )
            st.latex(
                r"\xi^{T}L=0,"
                r"\qquad"
                r"\sum_i\xi_i=1,"
                r"\qquad"
                r"\Xi=\operatorname{diag}(\xi)"
            )
            st.latex(
                r"S=\frac{\Xi L+L^{T}\Xi}{2}"
            )
            st.latex(
                r"M=\Xi^{-1/2}S\Xi^{-1/2}"
            )
            st.latex(
                r"\kappa=\lambda_2(M)"
            )

            st.markdown(
                """
                **Components**

                - `A` = directed weighted adjacency matrix.
                - `D` = diagonal matrix associated with the directed Laplacian.
                - `L = D − A` = directed weighted Laplacian.
                - `ξ` = positive normalized stationary/influence vector satisfying
                  `ξᵀL = 0`.
                - `Ξ = diag(ξ)`.
                - `S` = stationary-weighted symmetrization of the directed
                  Laplacian.
                - `M` = normalized symmetric matrix.
                - `λ₂(M)` = second-smallest eigenvalue of `M`.
                - `κ` = generalized algebraic connectivity.

                **Interpretation:** larger κ means stronger global spectral
                cohesion; smaller κ indicates a stronger global bottleneck.

                κ is recomputed from the complete perturbed graph at every
                attack step. It becomes undefined (`NaN`) when the graph no
                longer satisfies the required spectral feasibility conditions,
                especially strong connectivity.

                **Reference:** Wu, X., Liu, X., Zhang, C., Chen, T. & Lu, W.
                (2026), *Spectral Sensitivity of Directed Weighted Networks:
                Why Weakening Edges May Trigger Synchronization*, Section 3,
                Equation (3).
                """
            )

        # ----------------------------------------------------
        # Gamma
        # ----------------------------------------------------
        with st.expander("Additional notebook outcome: spectral γ"):
            st.markdown(
                """
                For the nonsymmetric directed Laplacian `L`, the notebook defines:
                """
            )
            st.latex(
                r"\gamma="
                r"\min_{\substack{\lambda\in\sigma(L)\\\lambda\ne0}}"
                r"\operatorname{Re}(\lambda)"
            )
            st.markdown(
                """
                **Components**

                - `σ(L)` = spectrum (set of eigenvalues) of the directed
                  Laplacian.
                - the zero eigenvalue is excluded.
                - `Re(λ)` = real part of an eigenvalue.
                - `γ` = smallest nonzero real part.

                **Interpretation:** γ describes the slowest exponential decay
                mode of the linear consensus dynamics used in the spectral
                framework; larger γ corresponds to faster convergence.

                **Reference:** Wu et al. (2026), Section 4.4. The notebook
                computes γ as a full graph outcome even though it is not central
                in the compact final visual library.
                """
            )

        st.info(
            "Robustness inference uses the **magnitude of departure from each "
            "realization's own baseline**, not an assumption that every Y must "
            "decrease. Raw and signed-change figures preserve the direction of "
            "the response."
        )

    # ========================================================
    # TAB 3 — ATTACKS & RANKINGS
    # ========================================================
    with tab_attacks:
        st.subheader("Attack families and ranking rules")
        st.markdown(
            """
            All rankings are **static**: they are computed once on the original
            unperturbed graph `G₀`, and the resulting order is held fixed during
            the attack.
            """
        )

        # ----------------------------------------------------
        # Node removal
        # ----------------------------------------------------
        with st.expander("1. Progressive node removal", expanded=True):
            st.markdown(
                """
                If the static node order is
                `(v₁, v₂, …)`, after removing the first `k` nodes the current
                graph is:
                """
            )
            st.latex(
                r"G_k="
                r"G_0\left[V\setminus\{v_1,\ldots,v_k\}\right]"
            )
            st.latex(
                r"f_k=\frac{k}{n_0}"
            )
            st.markdown(
                """
                where `f_k` is the fraction of original nodes removed. The
                experiment continues up to `f = 0.80`.

                The final primary visual library emphasizes three node rankings.
                """
            )

            st.markdown("#### Random ranking")
            st.markdown(
                """
                Nodes are shuffled with a seeded random generator. There is no
                centrality formula; the stochastic order is repeated five times
                within each network realization and averaged before inference.
                """
            )

            st.markdown("#### Out-strength ranking")
            st.latex(
                r"s_i^{out}=\sum_j w_{ij}"
            )
            st.markdown(
                """
                - `w_ij` = weight sent from node `i` to node `j`.
                - `s_i^out` = total outgoing weight of node `i`.
                - nodes are removed in **descending** out-strength order.

                The same strength definition is also used in the Yuan
                assortativity framework. **Reference:** Yuan et al. (2021),
                Section 2.
                """
            )

            st.markdown("#### Weighted Slack ranking")
            st.latex(
                r"T_j=\sum_h w_{hj}"
            )
            st.latex(
                r"\mathrm{Slack}_{ij}="
                r"\frac{T_j-w_{ij}}{\theta T_j},"
                r"\qquad \theta=0.70"
            )
            st.latex(
                r"\beta_{ij}="
                r"\frac{w_{ij}}{s_i^{out}},"
                r"\qquad"
                r"\mathrm{Slack}_i^{W}="
                r"\sum_j\beta_{ij}\mathrm{Slack}_{ij}"
            )
            st.markdown(
                """
                **Components**

                - `T_j` = total incoming weight received by target node `j`.
                - `w_ij` = weight of edge `i → j`.
                - `θ = 0.70` = quota/Slack parameter used in this experiment.
                - `β_ij` = share of node `i`'s outgoing strength carried by edge
                  `i → j`.
                - `Slack_ij` = edge-level remaining capacity relative to the
                  quota-scaled target total.
                - `Slack_i^W` = outgoing-weighted average Slack of node `i`.

                **Ranking rule:** **lower Slack = more pivotal**, so nodes are
                attacked in ascending `Slack_i^W`.

                The notebook contains the implemented formula directly; it does
                not attach a separate bibliographic reference to this function.
                """
            )

            st.info(
                "Node rankings are computed on the **LFR graph only** and the "
                "same node identity/order is applied to its matched NULL. This "
                "implements the matched-node perturbation design because LFR and "
                "NULL share the same node set."
            )

        # ----------------------------------------------------
        # Redistribution
        # ----------------------------------------------------
        with st.expander("2. Node removal with proportional redistribution"):
            st.markdown(
                """
                Node `v` is removed, but weight that surviving source `u` was
                sending to `v` is redistributed across `u`'s surviving outgoing
                edges.

                Let:
                """
            )
            st.latex(
                r"L_u=w_{uv}"
            )
            st.latex(
                r"S_u="
                r"\sum_{k\in N^{out}(u)\setminus\{v\}}w_{uk}"
            )
            st.latex(
                r"w_{uk}^{\,new}="
                r"w_{uk}"
                r"+"
                r"L_u\frac{w_{uk}}{S_u}"
            )
            st.markdown(
                """
                **Components**

                - `L_u` = weight lost by source `u` because edge `u → v`
                  disappears.
                - `N^out(u)` = outgoing neighbours of `u`.
                - `S_u` = total weight on `u`'s surviving outgoing edges.
                - `w_uk / S_u` = existing proportional share of surviving edge
                  `u → k`.
                - the lost flow is reallocated using those shares.

                Example: surviving outgoing weights 6 and 4 have shares 60% and
                40%. If 10 units are lost, the two surviving edges receive +6
                and +4.

                The **topology after removal is the same as ordinary node
                removal**; redistribution changes surviving weights, not
                surviving edge identities. Therefore a purely unweighted
                topological outcome can behave identically under removal and
                redistribution.
                """
            )

        # ----------------------------------------------------
        # Betweenness ranking
        # ----------------------------------------------------
        with st.expander("Betweenness rankings: what is being targeted?"):
            st.markdown(
                """
                The notebook uses weighted shortest paths by converting edge
                strength to effective distance:
                """
            )
            st.latex(r"\ell_e=\frac{1}{w_e}")
            st.markdown(
                """
                Hence a strong edge has a short effective distance.

                **Node betweenness** (implemented in the notebook, although not
                emphasized in the final 10 primary visual configurations) can
                be interpreted as:
                """
            )
            st.latex(
                r"C_B(v)="
                r"\sum_{\substack{s\ne t\\s,t\ne v}}"
                r"\frac{\sigma_{st}(v)}{\sigma_{st}}"
            )
            st.markdown(
                """
                **Weighted directed edge betweenness**, which is used in the
                final edge attacks, can be interpreted as:
                """
            )
            st.latex(
                r"C_B(e)="
                r"\sum_{s\ne t}"
                r"\frac{\sigma_{st}(e)}{\sigma_{st}}"
            )
            st.markdown(
                """
                **Components**

                - `σ_st` = number of shortest directed weighted paths from
                  source `s` to target `t`.
                - `σ_st(v)` = number of those shortest paths passing through
                  node `v`.
                - `σ_st(e)` = number passing through edge `e`.
                - shortest paths use `ℓ_e = 1/w_e`.
                - the notebook requests the **normalized** NetworkX
                  betweenness score.

                **Ranking rule:** higher betweenness is attacked first because
                those nodes/edges lie on more shortest directed routes.

                **Implementation:** NetworkX `betweenness_centrality` and
                `edge_betweenness_centrality`. The simulation notebook does not
                cite a separate betweenness paper in this section.
                """
            )

        # ----------------------------------------------------
        # Progressive edge weakening
        # ----------------------------------------------------
        with st.expander("3. Progressive ranked-edge weakening"):
            st.markdown(
                """
                Let the static edge ranking be `(e₁, e₂, …, e_m)`. At fraction
                `f_k = k/m`, the first `k` ranked edges have their weight halved:
                """
            )
            st.latex(
                r"w_e^{(k)}="
                r"\begin{cases}"
                r"0.5\,w_e^{(0)}, & e\in\{e_1,\ldots,e_k\},\\"
                r"w_e^{(0)}, & \text{otherwise.}"
                r"\end{cases}"
            )
            st.latex(r"f_k=\frac{k}{m}")
            st.markdown(
                """
                The experiment weakens progressively more edges up to 80% of the
                edge set.

                The two primary rankings shown in the final dashboard are:

                - **random edge order**;
                - **weighted directed edge betweenness**, highest first.

                Edge rankings are calculated **separately for LFR and NULL**
                because the degree-preserving rewiring changes the actual edge
                identities.
                """
            )

        # ----------------------------------------------------
        # Fixed subset
        # ----------------------------------------------------
        with st.expander("4. Fixed edge-subset deterioration"):
            st.markdown(
                """
                This attack holds the attacked edge identities fixed and changes
                **severity**, not the number of attacked edges.

                If `S` is the selected subset:
                """
            )
            st.latex(
                r"|S|="
                r"\left\lceil0.25\,m\right\rceil"
            )
            st.latex(
                r"w_e(\alpha)="
                r"\begin{cases}"
                r"\alpha w_e(0), & e\in S,\\"
                r"w_e(0), & e\notin S,"
                r"\end{cases}"
            )
            st.latex(r"\mathrm{severity}=1-\alpha")
            st.markdown(
                """
                **Components**

                - `m` = number of edges in the current graph before attack.
                - `S` = one fixed subset containing 25% of the edges.
                - `α` = remaining-weight multiplier.
                - `severity = 1−α` = deterioration shown on the x-axis.

                Two subset-selection rules are used:

                - **fixed random subset**;
                - **fixed weighted-betweenness subset:** the 25% of edges with
                  the largest weighted directed edge-betweenness scores.

                **Historical naming warning:** saved ranking names still contain
                `10pct`, but the actual parameter used in the final experiment
                is **0.25 = 25%**.
                """
            )

        # ----------------------------------------------------
        # Spectral ranking formulas
        # ----------------------------------------------------
        with st.expander("Advanced implemented rankings: spectral κ and γ sensitivity"):
            st.markdown(
                """
                These rankings are implemented in the simulation notebook but
                are not among the main edge-ranking combinations emphasized in
                the compact final dashboard.

                For a directed edge `j → i`, the perturbation model is:
                """
            )
            st.latex(
                r"A(\varepsilon)=A+\varepsilon E_{ij}"
            )

            st.markdown("#### γ sensitivity")
            st.latex(
                r"\frac{\partial\gamma}{\partial\varepsilon}="
                r"\operatorname{Re}"
                r"\left[\overline{y_i}(x_i-x_j)\right]"
            )
            st.markdown(
                """
                - `x` = right eigenvector of the Laplacian eigenvalue defining γ.
                - `y` = corresponding left eigenvector, normalized so
                  `yᴴx = 1`.
                - positive sensitivity means strengthening the edge locally
                  increases γ; therefore weakening it tends to decrease γ to
                  first order.

                **Reference:** Wu et al. (2026), Section 4.4, Equation (8).
                """
            )

            st.markdown("#### κ sensitivity")
            st.latex(
                r"\frac{\partial\kappa}{\partial\varepsilon}"
                r"="
                r"\xi_i y_i(y_i-y_j)"
                r"+"
                r"\frac{1}{2}y^TDCy"
            )
            st.latex(
                r"C=\Xi L-L^T\Xi,"
                r"\qquad"
                r"D=\operatorname{diag}(\xi')\Xi^{-1},"
                r"\qquad"
                r"\xi'=\frac{\partial\xi}{\partial\varepsilon}"
            )
            st.markdown(
                """
                - first term = local directed cut-energy contribution;
                - second term = global stationary-redistribution contribution;
                - large positive sensitivity is prioritized by a
                  damage-oriented weakening attack.

                **Reference:** Wu et al. (2026), Theorem 1 / Equation (5),
                Equations (6)–(7), and the single-edge formulation discussed in
                the notebook.
                """
            )

        st.subheader("Attack-family cheat sheet")
        attack_table = pd.DataFrame(
            [
                [
                    "Node removal",
                    "Which nodes disappear?",
                    "Fraction of nodes removed",
                    "Random; weighted Slack; out-strength",
                    "Delete ranked nodes",
                ],
                [
                    "Node redistribution",
                    "Can lost flow be rerouted after node loss?",
                    "Fraction of nodes removed",
                    "Same node rankings",
                    "Delete node + proportionally reroute lost incoming flow",
                ],
                [
                    "Progressive edge weakening",
                    "What if increasingly many important edges weaken?",
                    "Fraction of edges weakened",
                    "Random edge; weighted edge betweenness",
                    "Top-k attacked edges × 0.5",
                ],
                [
                    "Fixed subset deterioration",
                    "What if one fixed subset progressively deteriorates?",
                    "Deterioration severity",
                    "Random 25%; top-betweenness 25%",
                    "Same selected edges × α",
                ],
            ],
            columns=[
                "Family",
                "Question",
                "x-axis",
                "Primary ranking / rule",
                "Perturbation",
            ],
        )
        show_table(attack_table, height=330)


        st.subheader("Illustrative attacks in action")
        st.markdown(
            """
            These GIFs are **method illustrations**, not inferential summaries.
            They show one strong-community example (`μ = 0.075`) so that the
            perturbation itself can be inspected directly.

            Unlike the dedicated attack-mechanism figures elsewhere in the app,
            these animations do **not** force the NULL nodes into separated
            community clusters. This makes the rewired NULL topology visually
            explicit.

            Select an attack below. The LFR realization is shown on the left and
            its corresponding NULL example on the right.
            """
        )

        method_attack_gifs = {
            "Node removal": (
                "01_mu_0p075_node_removal_lfr.gif",
                "02_mu_0p075_node_removal_null.gif",
            ),
            "Node redistribution": (
                "03_mu_0p075_node_redistribution_lfr.gif",
                "04_mu_0p075_node_redistribution_null.gif",
            ),
            "Progressive edge weakening": (
                "05_mu_0p075_edge_weakening_lfr.gif",
                "06_mu_0p075_edge_weakening_null.gif",
            ),
            "Fixed random 25% subset deterioration": (
                "07_mu_0p075_edge_weakening_random_subset_lfr.gif",
                "08_mu_0p075_edge_weakening_random_subset_null.gif",
            ),
        }

        attack_demo = st.selectbox(
            "Illustrative attack",
            list(method_attack_gifs.keys()),
            key="methods_attack_demo",
        )

        lfr_gif, null_gif = method_attack_gifs[attack_demo]
        gif_left, gif_right = st.columns(2)

        with gif_left:
            st.markdown("#### LFR")
            _show_method_asset(
                lfr_gif,
                caption=f"{attack_demo} — representative LFR realization.",
            )

        with gif_right:
            st.markdown("#### Matched NULL")
            _show_method_asset(
                null_gif,
                caption=f"{attack_demo} — corresponding NULL illustration.",
            )

        st.caption(
            "These animations explain the mechanics of the attack. Formal "
            "conclusions come from all 40 independent realizations per "
            "modularity regime and the paired/ANOVA analyses."
        )

        with st.expander("Optional static attack snapshots"):
            st.markdown(
                """
                Static snapshots are useful when you want to inspect one attack
                state carefully or use a still image in a presentation. The GIFs
                remain the primary method illustration because they show the
                complete perturbation process.
                """
            )

            static_left, static_right = st.columns(2)

            with static_left:
                st.markdown("**Node removal snapshot**")
                _show_method_asset(
                    "node_removal_static.png",
                    caption="Representative static node-removal state.",
                )

            with static_right:
                st.markdown("**Fixed-subset deterioration snapshot**")
                _show_method_asset(
                    "fixed_random_subset_static.png",
                    caption=(
                        "Representative fixed random 25% edge-subset "
                        "deterioration state."
                    ),
                )

    # ========================================================
    # TAB 4 — NULL MODEL
    # ========================================================
    with tab_null:
        st.subheader("Matched directed degree-preserving NULL")

        st.markdown(
            """
            The NULL asks whether an observed robustness pattern is specifically
            associated with organized LFR community architecture or could arise
            simply from the degree sequence and edge-weight distribution.

            For two directed edges:
            """
        )
        st.latex(
            r"(a\rightarrow b,\;c\rightarrow d)"
            r"\mapsto"
            r"(a\rightarrow d,\;c\rightarrow b)"
        )

        left, right = st.columns(2)

        with left:
            st.markdown(
                """
                ### Preserved exactly

                - same node set;
                - same node attributes, including planted labels;
                - exact in-degree of every node;
                - exact out-degree of every node;
                - same number of edges;
                - exact same multiset of edge weights.
                """
            )

        with right:
            st.markdown(
                """
                ### Intentionally destroyed

                - planted community topology;
                - original topology/community alignment;
                - original topology/weight association.

                After rewiring, the original weight multiset is shuffled over the
                rewired edges.
                """
            )

        st.markdown(
            """
            Self-loops and duplicate edges are rejected. The implementation
            targets approximately `10 × |E|` accepted directed swaps, subject to
            a larger maximum-attempt budget.
            """
        )


        st.markdown("### Visualizing what the NULL construction changes")
        st.markdown(
            """
            The next two figures are particularly important for interpreting the
            NULL correctly.

            **First figure:** the same planted community colors are retained on
            both sides. The LFR topology visibly respects those communities,
            whereas the degree-preserving rewiring creates many cross-community
            connections in the NULL.

            **Second figure:** a labeled subset makes the matching explicit:
            the same node IDs and the same planted community labels are present
            in both graphs, but their edge relationships have changed.

            This also explains why some attack animations can be misleading if
            the same community-separated coordinates are imposed on LFR and
            NULL: node positions are only a visualization choice. The **edges**
            determine whether the topology actually respects the planted
            communities.
            """
        )

        _show_method_asset(
            "null_community_structure.png",
            caption=(
                "Official directed weighted LFR versus its degree-preserving "
                "NULL. Node colors retain the planted labels; rewiring disrupts "
                "the original community-organized edge structure."
            ),
        )

        _show_method_asset(
            "lfr_null_labeled_sample.png",
            caption=(
                "Labeled LFR/NULL sample: same node IDs and planted community "
                "labels, different rewired edge topology."
            ),
        )

        st.info(
            "A NULL displayed under a row labelled, for example, `Qw ≈ 0.690` "
            "means 'the NULL matched to the LFR regime whose realized Qw was "
            "≈ 0.690'. It does **not** mean that the rewired NULL itself retains "
            "Qw = 0.690."
        )

        st.subheader("Why matching matters")
        st.latex(
            r"\Delta AUC_i="
            r"AUC_{LFR,i}-AUC_{NULL,i}"
        )
        st.markdown(
            """
            Each LFR realization has its own structural control. The paired
            design therefore uses the within-pair difference above. Dependence
            inside an LFR–NULL pair is intentional and handled by the paired
            test; independence is required between the 40 matched pairs.
            """
        )

    # ========================================================
    # TAB 5 — SOFTWARE & REFERENCES
    # ========================================================
    with tab_software:
        st.subheader("Main computational tools")

        software_table = pd.DataFrame(
            [
                ["Official weighted-directed LFR C++ benchmark", "Generate community-structured weighted-directed networks"],
                ["NetworkX", "Directed graph structure, components, reachability, Dijkstra paths, betweenness, assortativity, Louvain"],
                ["NumPy", "Numerical arrays, random generators, numerical summaries"],
                ["pandas", "Long-form result tables, aggregation and persistence"],
                ["SciPy", "Spectral linear algebra and classical statistical tests"],
                ["statsmodels", "Welch ANOVA and Tukey HSD support"],
                ["Matplotlib", "Scientific figures"],
                ["Google Colab + Drive", "Long simulation execution and persistent checkpoints"],
                ["Streamlit", "Interactive dashboard"],
            ],
            columns=["Tool", "Role in the workflow"],
        )
        show_table(software_table, height=390)

        st.markdown(
            """
            ### References explicitly used for the principal formulas / methods

            - **Newman, M. E. J. (2003).** *Mixing patterns in networks.*
              Categorical assortativity and the mixing-matrix formula used by
              both planted community-assortativity outcomes.
            - **Yuan, Y., Yan, J. & Zhang, P. (2021).** *Assortativity Measures
              for Weighted and Directed Networks.* Weighted directed Pearson
              strength assortativity; the experiment uses the out–in version.
            - **Wu, X., Liu, X., Zhang, C., Chen, T. & Lu, W. (2026).**
              *Spectral Sensitivity of Directed Weighted Networks: Why
              Weakening Edges May Trigger Synchronization.* Spectral κ, γ and
              their edge sensitivities.
            - **Blondel, V. D., Guillaume, J.-L., Lambiotte, R. & Lefebvre,
              E. (2008).** *Fast unfolding of communities in large networks.*
              Louvain community detection used for the dynamic-community
              sensitivity analysis.
            - **Lancichinetti, A., Fortunato, S. & Radicchi, F. (2008).**
              *Benchmark graphs for testing community detection algorithms.*
              LFR benchmark family.

            ### Implementation-only definitions

            GSCC ratio, directed reachability, weighted global efficiency and
            NetworkX betweenness are implemented directly with NetworkX graph
            algorithms in the notebook. The simulation notebook does not attach
            a separate bibliographic citation to those particular diagnostic
            functions; the formulas shown in this guide document exactly how
            they are calculated in this experiment.
            """
        )

        st.caption(
            "For manuscript use, copy the complete bibliographic entries from "
            "the paper/reference manager rather than relying on the abbreviated "
            "dashboard citations."
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
