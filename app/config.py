from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

APP_TITLE = "Network Robustness Dashboard"
APP_SUBTITLE = (
    "Weighted-directed LFR networks versus matched degree-preserving NULL models "
    "across modularity regimes and attack strategies."
)

PRIMARY_OUTCOME = "weighted_directed_community_assortativity"

ATTACK_ORDER = [
    "node_removal",
    "node_redistribution",
    "edge_weakening",
    "edge_weakening_random_subset",
]

ATTACK_LABELS = {
    "node_removal": "Node removal",
    "node_redistribution": "Node removal with redistribution",
    "edge_weakening": "Progressive ranked-edge weakening",
    "edge_weakening_random_subset": "Fixed edge-subset weakening",
}

RANKING_LABELS = {
    "random": "Random",
    "weighted_slack": "Weighted Slack",
    "out_strength": "Out-strength",
    "random_edge": "Random edge",
    "weighted_edge_betweenness": "Weighted edge betweenness",
    "random_fixed_10pct": "Fixed random subset (25% of edges)",
    "weighted_edge_betweenness_fixed_10pct":
        "Fixed weighted-betweenness subset (25% of edges)",
}

OUTCOME_LABELS = {
    "weighted_directed_community_assortativity":
        "Weighted-directed community assortativity",
    "community_assortativity":
        "Community assortativity",
    "yuan_out_in_strength_assortativity":
        "Yuan out–in strength assortativity",
    "spectral_kappa":
        "Spectral kappa",
    "gscc_ratio":
        "GSCC ratio",
    "reachability":
        "Reachability",
    "weighted_efficiency":
        "Weighted efficiency",
    "weighted_directed_community_assortativity_louvain_dynamic":
        "Weighted-directed community assortativity (dynamic Louvain)",
    "community_assortativity_louvain_dynamic":
        "Community assortativity (dynamic Louvain)",
}

COMMUNITY_LABELS = {
    "planted": "Planted / ground-truth communities",
    "louvain": "Dynamic weighted-Louvain communities",
}
