# Network Robustness Dashboard

Fresh Streamlit application for the final 40-run weighted-directed LFR versus
matched degree-preserving NULL experiment.

## Folder structure

Copy this starter into the folder that already contains `data/`, `metadata/`
and `visuals/`.

```text
network-robustness-dashboard/
├── streamlit_app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── labels.py
│   ├── data_loader.py
│   ├── components.py
│   └── pages.py
├── scripts/
│   └── validate_bundle.py
├── data/
├── metadata/
└── visuals/
```

## 1. Validate the bundle

```bash
python3 scripts/validate_bundle.py
```

## 2. Create a local environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Run the app

```bash
streamlit run streamlit_app.py
```

## 4. GitHub

After the local app works:

```bash
git init
git add .
git commit -m "Initial network robustness dashboard"
git branch -M main
```

Create an empty GitHub repository, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/network-robustness-dashboard.git
git push -u origin main
```

For Streamlit Community Cloud use `streamlit_app.py` as the entry point.

## Scientific interpretation

Primary outcome:

`weighted_directed_community_assortativity`

Primary robustness measure:

`auc_abs_delta = ∫ |Y(x) - Y(0)| dx`

Paired comparison:

`ΔAUC = AUC_LFR - AUC_NULL`

- `ΔAUC < 0` → LFR relatively more robust.
- `ΔAUC > 0` → LFR relatively more disrupted.

Historical labels containing `10pct` are retained, although the final fixed
subset contains 25% of edges.
