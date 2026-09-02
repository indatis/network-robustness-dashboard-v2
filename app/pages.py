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
# METHODS & METRIC GUIDE
# ============================================================

def page_methods(data, visual_index):
    st.header("Methods & metric guide")
    st.caption(
        "A compact reference for the network generator, matched NULL, "
        "outcome variables, attacks, rankings, and inferential workflow."
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

    st.markdown(
        """
        The full experiment can be read as one sequence:
        """
    )

    step_titles = [
        "1. Generate",
        "2. Match",
        "3. Perturb",
        "4. Measure",
        "5. Summarize",
        "6. Infer",
    ]
    step_text = [
        "Weighted-directed LFR network",
        "Degree-preserving NULL",
        "Node / edge attack",
        "Compute Y(x) at each step",
        "Trajectory → AUC",
        "Paired tests + ANOVA",
    ]

    cols = st.columns(6)
    for col, title, text in zip(cols, step_titles, step_text):
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
                    <span style="font-size:0.92rem;">{text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        **Interpretation:** first create a structured network and its matched
        control, expose both to controlled perturbations, track network outcomes
        across attack intensity, reduce each trajectory to one robustness AUC per
        realization, and then answer two complementary questions:

        - **LFR vs NULL:** does organized community structure make the network
          more or less robust than its matched control?
        - **Across modularity:** does robustness change as the LFR community
          structure becomes weaker or stronger?
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
            "**Do not confuse the 5 random repetitions with independent sample "
            "size.** They repeat stochastic attack orders inside the same network "
            "realization and are averaged before inference. The independent units "
            "are the 40 LFR realizations per modularity configuration."
        )

        st.markdown(
            """
            ### Mixing parameter versus realized modularity

            The LFR input mixing parameter and realized modularity move in
            opposite directions:
            """
        )

        st.latex(r"\mu \downarrow \quad \Longrightarrow \quad Q_w \uparrow")

        st.markdown(
            """
            Therefore `μ = 0.075` represents the strongest community structure
            in the active transition, while `μ = 0.300` represents the weakest.

            The dashboard plots often use **realized weighted modularity `Qw`**
            on the x-axis because it describes the structure actually generated,
            rather than only the requested generator parameter.
            """
        )

        with st.expander("Why do some descriptive dashboard plots show only three rows?"):
            st.markdown(
                """
                Some descriptive trajectory panels display only three
                representative regimes to remain readable:

                - **weak structure:** μ = 0.300, Qw ≈ 0.460
                - **intermediate structure:** μ = 0.150, Qw ≈ 0.620
                - **strong structure:** μ = 0.075, Qw ≈ 0.690

                Those figures are illustrative summaries. The paired tests and
                across-modularity ANOVA use **all seven modularity
                configurations and all 40 independent realizations per
                configuration**.
                """
            )

    # ========================================================
    # TAB 2 — OUTCOMES
    # ========================================================
    with tab_outcomes:
        st.subheader("Outcome variables Y")

        st.markdown(
            """
            At every perturbation state the notebook computes a collection of
            structural outcomes, denoted generically by `Y(x)`. Each outcome
            captures a different aspect of network robustness.
            """
        )

        with st.expander(
            "Weighted-directed community assortativity — PRIMARY",
            expanded=True,
        ):
            st.markdown(
                """
                **Question:** Does the network's **total directed edge weight**
                remain preferentially inside communities?

                For each edge `u → v`, its weight is added to a
                source-community → target-community mixing matrix. The
                assortativity coefficient compares observed within-community
                weighted flow with the amount expected from the source and
                target community marginals.

                **Interpretation**

                - positive → more total weight remains within communities than
                  expected;
                - near zero → little weighted community preference;
                - negative → relatively more weight flows between communities.

                **Why this is the primary outcome:** the experiment is explicitly
                weighted and directed, and the research question concerns
                preservation/disruption of modular organization. This measure
                therefore uses all three ingredients: **direction, weight, and
                community membership**.

                The primary version uses the **known planted LFR communities**.
                """
            )

        with st.expander("Unweighted community assortativity"):
            st.markdown(
                """
                **Question:** Do directed edges connect nodes in the same
                community more often than expected?

                This version uses the existence of edges and their community
                labels but **ignores edge weights**.

                - positive → assortative community mixing;
                - near zero → no clear community mixing preference;
                - negative → relatively more between-community connections.

                **Important consequence:** weakening an edge without deleting it
                does not change this unweighted measure, because the topology is
                unchanged. Node removal can change it because nodes and edges
                disappear.
                """
            )

        with st.expander("Dynamic weighted-Louvain community outcomes"):
            st.markdown(
                """
                Two additional community outcomes repeat the unweighted and
                weighted-directed assortativity calculations using a
                **weighted Louvain partition re-detected at every perturbation
                state**.

                This answers a different question:

                > If communities are allowed to reorganize after damage, does
                > the observed community-mixing pattern remain robust?

                The planted-community outcomes keep the original benchmark
                partition fixed. The dynamic-Louvain outcomes allow the
                partition to adapt. Louvain is run once per graph state and the
                same detected partition is reused for both dynamic community
                outcomes.

                In this dashboard, planted weighted-directed assortativity is
                the primary benchmark outcome; dynamic Louvain is a
                sensitivity/secondary analysis.
                """
            )

        with st.expander("Yuan out–in strength assortativity"):
            st.markdown(
                """
                **Question:** Do nodes that send a large total weight tend to
                connect to nodes that receive a large total weight?

                For each directed edge `u → v`:

                - source feature = out-strength of `u`;
                - target feature = in-strength of `v`;
                - observation weight = edge weight `w_uv`.

                The final coefficient is a **weighted Pearson correlation**.

                - positive → strong senders tend to connect to strong receivers;
                - near zero → no clear linear strength association;
                - negative → strong senders tend to connect to weak receivers
                  (or vice versa).

                This is a numeric strength-assortativity measure and is
                conceptually different from categorical community assortativity.
                """
            )

        with st.expander("GSCC ratio"):
            st.markdown(
                """
                **GSCC = Giant Strongly Connected Component.**

                In a directed strongly connected component, every node can reach
                every other node by following directed paths.

                The metric is:

                `size of largest strongly connected component / original number of nodes`

                - 1 → all original nodes belong to one mutually reachable core;
                - 0.5 → the largest strongly connected core contains half of the
                  original nodes;
                - near 0 → strong directed fragmentation.

                The denominator always uses the original network size, so node
                loss cannot make the ratio look artificially healthy.
                """
            )

        with st.expander("Directed reachability ratio"):
            st.markdown(
                """
                **Question:** Among all possible ordered pairs of original
                nodes, what proportion can still communicate through at least
                one directed path?

                The denominator is fixed at `n₀(n₀−1)`.

                - 1 → every ordered pair is reachable;
                - 0.5 → half remain reachable;
                - 0 → no ordered pair remains reachable.

                Unlike GSCC ratio, reachability counts all reachable ordered
                pairs and therefore captures communication outside the single
                largest strongly connected component as well.
                """
            )

        with st.expander("Directed weighted global efficiency"):
            st.markdown(
                """
                **Question:** How efficiently can nodes reach one another through
                short, strong, directed weighted paths?

                Edge strength is converted to path cost using:
                """
            )
            st.latex(r"d_{uv}=\frac{1}{w_{uv}}")
            st.markdown(
                """
                A stronger edge therefore acts as a shorter effective distance.

                For each reachable ordered pair, the contribution is the inverse
                of its shortest-path distance. Unreachable pairs contribute zero,
                and the denominator remains `n₀(n₀−1)`.

                - larger efficiency → short/strong directed routes remain;
                - smaller efficiency → routes are weaker, longer, lost, or
                  unreachable.

                Because weighted path distances can be below 1, this weighted
                efficiency is **not necessarily bounded by 1**.
                """
            )

        with st.expander("Spectral κ (generalized algebraic connectivity)"):
            st.markdown(
                """
                **Question:** How strong is the network's weakest global
                spectral-connectivity / synchronization-related mode?

                The directed Laplacian is transformed using its stationary
                left-zero eigenvector and then symmetrized. `κ` is the
                second-smallest eigenvalue of the resulting matrix.

                - larger κ → stronger global spectral cohesion;
                - smaller κ → stronger bottleneck / weaker cohesion;
                - κ near zero → weak synchronization-related connectivity.

                The value is recomputed from the **complete perturbed graph** at
                every attack step. It is not merely an edge-sensitivity
                approximation.

                **Important:** κ is returned as undefined (`NaN`) when the
                perturbed graph no longer satisfies the required spectral
                feasibility conditions, especially strong connectivity.
                """
            )

        with st.expander("Additional notebook outcome: spectral γ"):
            st.markdown(
                """
                The simulation notebook also computes `spectral_gamma`, although
                it is not a central outcome in the current final visual library.

                `γ` is the smallest non-zero real part of the directed Laplacian
                spectrum and characterizes the slowest exponential decay mode of
                a linear consensus process.

                - larger γ → faster spectral convergence;
                - smaller γ → slower convergence;
                - near zero → very slow spectral mode.

                Like κ, it can become undefined when the perturbed network is no
                longer spectrally feasible.
                """
            )

        st.info(
            "Remember: the robustness analysis does not assume that every Y "
            "should always decrease under damage. Formal robustness uses the "
            "magnitude of departure from each realization's own baseline; raw "
            "and signed-change figures retain the direction of the response."
        )

    # ========================================================
    # TAB 3 — ATTACKS
    # ========================================================
    with tab_attacks:
        st.subheader("Attack families and ranking rules")

        st.markdown(
            """
            All targeted rankings are **static**: they are calculated once on the
            original unperturbed graph `G₀` and then kept fixed during the attack.
            This avoids changing the attack rule at every perturbation step.
            """
        )

        with st.expander("1. Progressive node removal", expanded=True):
            st.markdown(
                """
                Nodes are removed one by one according to a fixed ranking, up to
                **80% of the original nodes**.

                The final primary visual library emphasizes three rankings:

                **Random**
                - a seeded random node order;
                - repeated 5 times within the same realization and averaged
                  before inference.

                **Out-strength**
                - rank nodes by total outgoing edge weight;
                - highest out-strength removed first;
                - targets nodes that send the greatest total weight.

                **Weighted Slack**
                - for edge `i → j`, the notebook defines:
                """
            )
            st.latex(
                r"\mathrm{Slack}_{ij}"
                r"="
                r"\frac{T_j-w_{ij}}{\theta T_j},"
                r"\qquad \theta=0.70"
            )
            st.markdown(
                """
                where `T_j` is the total incoming weight of target `j`.

                Node Slack is the outgoing-weighted average of its edge Slack
                values. **Lower Slack = more pivotal**, so weighted-Slack attack
                removes the lowest-scoring nodes first.

                **Matching rule:** node rankings are computed on the **LFR graph
                only** and the same node order is then applied to its matched
                NULL. This ensures that the two graphs face the same node
                identities/order rather than independently optimized attacks.
                """
            )

        with st.expander("2. Node removal with proportional redistribution"):
            st.markdown(
                """
                The node is still removed, using the same ranking rules, but the
                experiment allows part of the lost flow to be rerouted.

                Suppose node `v` is removed and source node `u` had sent weight
                `w_lost` to `v`. The lost weight is redistributed across `u`'s
                surviving outgoing edges **proportionally to their current
                weights**.

                Simple example:

                - surviving outgoing weights from `u`: 6 and 4;
                - lost weight to removed node: 10;
                - surviving shares are 60% and 40%;
                - redistributed weights added are 6 and 4.

                This attack asks whether the network can preserve function when
                connections are **reallocated after node loss**, rather than
                simply destroyed.

                **Important:** the surviving topology after node removal is the
                same as ordinary node removal; redistribution changes weights,
                not which surviving edges exist. Consequently, a purely
                unweighted topological outcome may behave identically under
                removal and redistribution.
                """
            )

        with st.expander("3. Progressive ranked-edge weakening"):
            st.markdown(
                """
                Edges are ranked once. As attack intensity increases,
                progressively more ranked edges enter the attacked set.

                Every attacked edge is weakened once using:
                """
            )
            st.latex(r"w_{\mathrm{new}}=0.5\,w_{\mathrm{old}}")
            st.markdown(
                """
                The final visual library emphasizes:

                **Random edge**
                - random edge ordering.

                **Weighted edge betweenness**
                - edges are ranked by weighted directed edge-betweenness
                  centrality;
                - higher betweenness is attacked first;
                - shortest-path calculations use `distance = 1/weight`, so
                  strong edges behave as shorter connections.

                The x-axis for this family is the **fraction of edges that have
                been weakened**, up to 80%.

                Unlike node attacks, generic edge rankings are computed
                separately in LFR and NULL because rewiring changes the actual
                edge identities.
                """
            )

        with st.expander("4. Fixed edge-subset deterioration"):
            st.markdown(
                """
                This attack changes **severity**, not the number of attacked
                edges.

                First select one fixed subset of edges. Then keep those same edge
                identities throughout the curve and progressively reduce their
                weights:
                """
            )
            st.latex(r"w_e(\alpha)=\alpha\,w_e(0)")
            st.markdown(
                """
                The x-axis is deterioration severity:

                `severity = 1 − α`.

                Two subset rules are used:

                **Fixed random subset**
                - choose a random fixed subset of edges.

                **Fixed weighted-betweenness subset**
                - choose the top weighted-edge-betweenness edges.

                The current experiment selects **25% of all edges** in each
                graph. Historical file/ranking labels still contain `10pct` for
                backward compatibility, but the actual parameter value used is
                **0.25**.

                LFR and NULL select their own edge subsets because their rewired
                edge identities differ, while the requested subset fraction is
                the same.
                """
            )

        with st.expander("Additional ranking rules implemented in the notebook"):
            st.markdown(
                """
                The simulation code also implements additional node/edge
                rankings such as node out-degree, node weighted betweenness,
                edge weight, and spectral κ/γ edge-sensitivity rankings.

                The compact final dashboard intentionally focuses on the
                pre-specified attack/ranking combinations used for the primary
                robustness comparisons rather than exposing every implemented
                exploratory ranking.
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
                    "Node deleted",
                ],
                [
                    "Node redistribution",
                    "Can lost flow be reallocated after node loss?",
                    "Fraction of nodes removed",
                    "Same node rankings",
                    "Node deleted + incoming lost weight rerouted",
                ],
                [
                    "Progressive edge weakening",
                    "What if increasingly many important edges weaken?",
                    "Fraction of edges weakened",
                    "Random edge; weighted edge betweenness",
                    "Each attacked edge × 0.5",
                ],
                [
                    "Fixed edge-subset deterioration",
                    "What if one fixed critical subset progressively deteriorates?",
                    "Deterioration severity",
                    "Fixed random 25%; fixed top-betweenness 25%",
                    "Same selected edges scaled by α",
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

    # ========================================================
    # TAB 4 — NULL MODEL
    # ========================================================
    with tab_null:
        st.subheader("Matched directed degree-preserving NULL")

        st.markdown(
            """
            The NULL is designed to answer:

            > Is an observed robustness pattern specifically associated with
            > organized LFR community architecture, or could it arise simply
            > from the degree sequence and edge-weight distribution?

            For each LFR realization, one matched NULL is created by directed
            edge swaps of the form:
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
                - same node attributes, including planted community labels;
                - each node's exact in-degree;
                - each node's exact out-degree;
                - same number of edges;
                - same multiset of edge weights;
                - consequently, same total weight and weight distribution.
                """
            )

        with right:
            st.markdown(
                """
                ### Intentionally destroyed

                - planted community topology;
                - alignment between topology and planted communities;
                - original topology–weight association.

                The original weights are shuffled across the rewired edges after
                the degree-preserving rewiring.
                """
            )

        st.markdown(
            """
            Self-loops and duplicate edges are avoided during rewiring. The
            experiment targets approximately `10 × |E|` accepted directed swaps,
            with a larger maximum-attempt budget to obtain substantial
            randomization.
            """
        )

        st.info(
            "The NULL retains the planted community labels as node attributes, "
            "but the rewiring destroys the topology that originally supported "
            "those communities. Thus a NULL plotted under the row labelled "
            "`Qw ≈ 0.690` means 'the NULL matched to the LFR regime with "
            "Qw ≈ 0.690'; it does not mean the NULL itself still has Qw = 0.690."
        )

        st.subheader("Why matching matters")

        st.markdown(
            """
            Because each LFR has a specifically constructed control, the paired
            analysis compares:

            `AUC_LFR,i − AUC_NULL,i`

            for each realization `i`.

            This removes much of the between-realization variability that would
            otherwise obscure the question of interest. The paired design handles
            dependence **within** LFR–NULL pairs; independence is required
            **between** the 40 matched pairs.
            """
        )

    # ========================================================
    # TAB 5 — SOFTWARE & REFERENCES
    # ========================================================
    with tab_software:
        st.subheader("Main computational tools")

        software_table = pd.DataFrame(
            [
                ["Official LFR C++ benchmark", "Generate weighted-directed benchmark networks"],
                ["NetworkX", "Directed graph representation, connectivity, shortest paths, betweenness, assortativity, Louvain"],
                ["NumPy", "Numerical arrays, random generators, numerical summaries"],
                ["pandas", "Long-form result tables, aggregation and persistence"],
                ["SciPy", "Spectral linear algebra and classical statistical tests"],
                ["statsmodels", "Welch ANOVA and Tukey HSD support"],
                ["Matplotlib", "Generation of the scientific figures"],
                ["Google Colab + Drive", "Long simulation execution and persistent pair-level checkpoints"],
                ["Streamlit", "Interactive dashboard for the compact final outputs"],
            ],
            columns=["Tool", "Role in the workflow"],
        )
        show_table(software_table, height=390)

        st.markdown(
            """
            ### Methodological references used by the implementation

            - **Lancichinetti, Fortunato & Radicchi (2008)** — LFR benchmark
              family for community-structured synthetic networks.
            - **Lancichinetti & Fortunato (2009)** — directed/weighted LFR
              benchmark extension.
            - **Newman (2003), _Mixing patterns in networks_** — categorical
              assortativity mixing-matrix formulation. The project's
              weighted-directed community assortativity adapts this logic by
              accumulating edge weights instead of edge counts.
            - **Yuan, Yan & Zhang (2021), _Assortativity Measures for Weighted
              and Directed Networks_** — weighted directed strength
              assortativity. The implemented default is out–in strength
              assortativity.
            - **Wu et al. (2026), _Spectral Sensitivity of Directed Weighted
              Networks: Why Weakening Edges May Trigger Synchronization_** —
              spectral κ/γ formulation and edge-sensitivity framework used in
              the notebook.
            - **Blondel, Guillaume, Lambiotte & Lefebvre (2008)** — Louvain
              community-detection method; the implementation uses NetworkX's
              weighted Louvain routine with resolution 1.0.
            """
        )

        st.caption(
            "The dashboard is explanatory documentation of the implemented "
            "workflow. For a manuscript, use the full bibliographic entries "
            "from the paper's reference list."
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
