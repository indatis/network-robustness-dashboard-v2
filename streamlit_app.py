from pathlib import Path
import streamlit as st

from app.config import APP_TITLE, APP_SUBTITLE, ROOT_DIR
from app.data_loader import load_app_data, build_visual_index
from app.pages import (
    page_overview,
    page_methods,
    page_results_explorer,
    page_paired_tests,
    page_modularity,
    page_animations,
    page_heatmaps,
    page_downloads,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

data = load_app_data(ROOT_DIR)
visual_index = build_visual_index(ROOT_DIR)

with st.sidebar:
    st.markdown("### Navigation")
    section = st.radio(
        "Section",
        [
            "Overview",
            "Methods & metrics",
            "Results explorer",
            "LFR vs NULL robustness",
            "Modularity effects",
            "Attack animations",
            "Heatmaps",
            "Downloads",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "Final 40-run LFR vs matched NULL experiment. "
        "Compact tables and pre-generated visuals only."
    )

if section == "Overview":
    page_overview(data, visual_index)
elif section == "Methods & metrics":
    page_methods(data, visual_index)
elif section == "Results explorer":
    page_results_explorer(data, visual_index)
elif section == "LFR vs NULL robustness":
    page_paired_tests(data, visual_index)
elif section == "Modularity effects":
    page_modularity(data, visual_index)
elif section == "Attack animations":
    page_animations(data, visual_index)
elif section == "Heatmaps":
    page_heatmaps(data, visual_index)
elif section == "Downloads":
    page_downloads(data, visual_index)
