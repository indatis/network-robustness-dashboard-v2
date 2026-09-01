from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import streamlit as st

from app.config import ATTACK_ORDER

def _safe_read_csv(path: Path):
    if not path or not path.exists():
        return None
    try:
        return pd.read_csv(
            path,
            keep_default_na=False,
            na_values=["", "NaN", "nan", "NA", "N/A", "<NA>"],
        )
    except Exception:
        return None

def _first_existing(root: Path, candidates):
    for rel in candidates:
        p = root / rel
        if p.exists():
            return p
    return None

@st.cache_data(show_spinner=False)
def load_app_data(root_dir: Path):
    root = Path(root_dir)
    candidates = {
        "figure_manifest": ["data/manifests/figure_manifest.csv"],
        "resolved_configs": ["data/visual_summary/resolved_attack_ranking_configurations.csv"],
        "all_curve_summary": ["data/visual_summary/ALL_OUTCOMES_curve_summary_40runs.csv"],
        "paired_deltas_rebuilt": ["data/visual_summary/paired_auc_deltas_rebuilt.csv"],
        "paired_tests_rebuilt": ["data/visual_summary/paired_auc_ttests_rebuilt.csv"],
        "paired_deltas": ["data/paired_tests/paired_auc_deltas.csv"],
        "paired_tests": [
            "data/paired_tests/paired_auc_ttests.csv",
            "data/paired_tests/primary_paired_auc_ttests.csv",
        ],
        "auc_summary": ["data/paired_tests/auc_summary.csv"],
        "auc_for_boxplot": ["data/paired_tests/auc_for_boxplot.csv"],
        "modularity_summary": ["data/network/modularity_regime_summary.csv"],
        "network_characteristics": ["data/network/network_characteristics.csv"],
        "anova_all": ["data/anova/03_ANOVA_across_modularity_ALL.csv"],
        "anova_descriptives": ["data/anova/02_group_descriptives_ALL.csv"],
        "tukey_all": ["data/anova/04_TUKEY_posthoc_ALL.csv"],
        "games_howell_all": ["data/anova/05_GAMES_HOWELL_posthoc_ALL.csv"],
        "primary_anova": ["data/anova/12_PRIMARY_WD_ASSORTATIVITY_ANOVA.csv"],
        "primary_tukey": ["data/anova/13_PRIMARY_WD_ASSORTATIVITY_TUKEY.csv"],
        "primary_games_howell": ["data/anova/14_PRIMARY_WD_ASSORTATIVITY_GAMES_HOWELL.csv"],
        "asset_inventory": ["metadata/asset_inventory.csv"],
    }
    out = {}
    for key, rels in candidates.items():
        path = _first_existing(root, rels)
        out[key] = _safe_read_csv(path)
        out[key + "_path"] = path
    return out

def _strip_num(stem):
    return re.sub(r"^\d+_", "", stem)

def _community(path):
    return "louvain" if "louvain_dynamic" in "/".join(path.parts).lower() else "planted"

def _parse_outcome_attack_ranking(core):
    for attack in sorted(ATTACK_ORDER, key=len, reverse=True):
        marker = f"_{attack}_"
        if marker in core:
            outcome, ranking = core.split(marker, 1)
            return outcome, attack, ranking
    return None, None, None

def _parse_outcome_attack(core):
    for attack in sorted(ATTACK_ORDER, key=len, reverse=True):
        marker = f"_{attack}"
        if core.endswith(marker):
            return core[:-len(marker)], attack
    return None, None

def _parse_visual(path, visuals_root):
    rel = path.relative_to(visuals_root)
    parts = rel.parts
    stem = _strip_num(path.stem)
    row = {
        "path": str(path),
        "relative_path": str(rel),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "community_family": _community(rel),
        "visual_family": None,
        "outcome": None,
        "attack_family": None,
        "ranking_metric": None,
        "scale": None,
        "display_name": path.stem.replace("_", " ").title(),
    }

    if parts[0] == "01_dashboard_panels":
        row["visual_family"] = "dashboard"
        row["scale"] = parts[2] if len(parts) >= 3 else None
        core = re.sub(r"^Y\d+L?_", "", stem)
        for suffix in ("_absolute_delta", "_signed_delta", "_raw"):
            if core.endswith(suffix):
                core = core[:-len(suffix)]
                break
        row["outcome"], row["attack_family"] = _parse_outcome_attack(core)

    elif parts[0] == "02_luisa_style":
        row["visual_family"] = "luisa"
        core = stem.removesuffix("_raw_signed_delta")
        row["outcome"], row["attack_family"], row["ranking_metric"] = _parse_outcome_attack_ranking(core)
        row["scale"] = "raw_signed_delta"

    elif parts[0] == "03_paired_delta_auc":
        row["visual_family"] = "paired_delta_auc"
        core = stem.removesuffix("_paired_delta_auc")
        row["outcome"], row["attack_family"], row["ranking_metric"] = _parse_outcome_attack_ranking(core)
        row["scale"] = "paired_delta_auc"

    elif parts[0] == "04_anova_boxplots_posthoc":
        row["visual_family"] = "anova"
        core = stem.removesuffix("_anova_boxplot_posthoc")
        row["outcome"], row["attack_family"], row["ranking_metric"] = _parse_outcome_attack_ranking(core)
        row["scale"] = "anova"

    elif parts[0] == "05_heatmaps":
        row["visual_family"] = "heatmap"

    elif parts[0] == "06_attack_mechanisms":
        row["visual_family"] = "gif_disruption"

    elif parts[0] == "07_attack_mechanisms_raw_Y":
        row["visual_family"] = "gif_raw_y"

    return row

@st.cache_data(show_spinner=False)
def _index(root_str):
    root = Path(root_str)
    visuals = root / "visuals"
    if not visuals.exists():
        return pd.DataFrame()

    rows = [
        _parse_visual(p, visuals)
        for p in visuals.rglob("*")
        if p.is_file() and p.suffix.lower() in {".png", ".gif"}
    ]
    return pd.DataFrame(rows)

def build_visual_index(root_dir):
    return _index(str(Path(root_dir).resolve()))

def filter_dataframe(df, filters):
    if df is None or df.empty:
        return df

    aliases = {
        "outcome": ["outcome", "metric", "outcome_name"],
        "attack_family": ["attack_family", "attack"],
        "ranking_metric": ["ranking_metric", "ranking", "configuration"],
        "graph_type": ["graph_type", "network", "graph"],
        "modularity_regime": ["modularity_regime", "regime"],
    }

    out = df.copy()
    for key, value in filters.items():
        if value is None:
            continue
        col = next((c for c in aliases.get(key, [key]) if c in out.columns), None)
        if col is None:
            continue
        out = out[
            out[col].astype(str).str.strip().str.lower()
            == str(value).strip().lower()
        ]
    return out
