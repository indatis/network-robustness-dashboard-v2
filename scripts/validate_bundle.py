from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

required_dirs = [
    ROOT / "data",
    ROOT / "metadata",
    ROOT / "visuals",
    ROOT / "visuals" / "01_dashboard_panels",
    ROOT / "visuals" / "02_luisa_style",
    ROOT / "visuals" / "03_paired_delta_auc",
    ROOT / "visuals" / "04_anova_boxplots_posthoc",
    ROOT / "visuals" / "05_heatmaps",
    ROOT / "visuals" / "06_attack_mechanisms",
    ROOT / "visuals" / "07_attack_mechanisms_raw_Y",
]

required_files = [
    ROOT / "data" / "visual_summary" / "ALL_OUTCOMES_curve_summary_40runs.csv",
    ROOT / "data" / "visual_summary" / "paired_auc_deltas_rebuilt.csv",
    ROOT / "data" / "visual_summary" / "paired_auc_ttests_rebuilt.csv",
    ROOT / "data" / "visual_summary" / "resolved_attack_ranking_configurations.csv",
    ROOT / "data" / "network" / "modularity_regime_summary.csv",
    ROOT / "data" / "network" / "network_characteristics.csv",
    ROOT / "data" / "anova" / "03_ANOVA_across_modularity_ALL.csv",
    ROOT / "data" / "anova" / "04_TUKEY_posthoc_ALL.csv",
    ROOT / "data" / "anova" / "05_GAMES_HOWELL_posthoc_ALL.csv",
    ROOT / "data" / "manifests" / "figure_manifest.csv",
]

missing = []
for p in required_dirs:
    if not p.is_dir():
        missing.append(str(p.relative_to(ROOT)) + "/")
for p in required_files:
    if not p.is_file():
        missing.append(str(p.relative_to(ROOT)))

visuals = [
    p for p in (ROOT / "visuals").rglob("*")
    if p.is_file() and p.suffix.lower() in {".png", ".gif"}
]
large = [
    (p, p.stat().st_size / 1024**2)
    for p in ROOT.rglob("*")
    if p.is_file() and p.stat().st_size >= 50 * 1024**2
]

print("=" * 70)
print("NETWORK ROBUSTNESS APP — BUNDLE VALIDATION")
print("=" * 70)
print("Root:", ROOT)
print("Visual assets found:", len(visuals))
print("Missing required items:", len(missing))
print("Files >= 50 MB:", len(large))

if missing:
    print("\nMissing:")
    for item in missing:
        print(" -", item)

if large:
    print("\nLarge files:")
    for p, mb in sorted(large, key=lambda x: x[1], reverse=True):
        print(f" - {p.relative_to(ROOT)}: {mb:.2f} MB")

if missing:
    sys.exit(1)

print("\n✓ Bundle structure looks ready.")
