FINAL VISUAL LIBRARY — 40-RUN HIGH-MODULARITY TRANSITION

Source run:
/content/drive/MyDrive/lfr_attack_outputs_high_transition/run_20260814_055017_969909

IMPORTANT
---------
The simulation is NOT rerun by this script.
The 4+ GB curves_long.csv is NOT loaded.
All-outcome curve means/SDs are rebuilt RAM-safely from the 280 completed pair checkpoints.

CURVE PANELS
------------
The old visual grammar is preserved with 3 representative levels:
- mu_0p300: mu=0.300, Qw=0.460
- mu_0p150: mu=0.150, Qw=0.620
- mu_0p075: mu=0.075, Qw=0.690

STATISTICAL FIGURES
-------------------
All seven modularity configurations are used.
Paired Delta-AUC = AUC_LFR - AUC_NULL, where AUC is area under |Y(x)-Y(0)|.
Positive Delta-AUC -> LFR accumulated more disruption / was less robust.
Negative Delta-AUC -> LFR accumulated less disruption / was more robust.

ANOVA figures compare AUC across the seven modularity configurations separately for LFR and NULL.
Post-hoc brackets compare the original high-modularity reference mu=.100 against other levels.
Tukey HSD is used when equal variances are not rejected; Games-Howell is used when Levene rejects equal variances.

FIGURE COUNTS
-------------
family
anova_boxplot_posthoc    90
anova_effect_heatmap      2
dashboard_panel          63
luisa_style              90
paired_delta_auc         90
paired_heatmap           20

KEY FILES
---------
00_data/ALL_OUTCOMES_curve_summary_40runs.csv
00_data/paired_auc_deltas_rebuilt.csv
00_data/paired_auc_ttests_rebuilt.csv
00_data/resolved_attack_ranking_configurations.csv
figure_manifest.csv
