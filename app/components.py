from pathlib import Path
import base64

import pandas as pd
import streamlit as st

from app.labels import (
    pretty_attack,
    pretty_ranking,
    pretty_outcome,
    pretty_community,
    pretty_scale,
)


def show_asset(path, caption=None):
    """Display static images normally and preserve GIF animation."""

    path = Path(path)

    if not path.exists():
        st.error(f"Asset not found: {path}")
        return

    if path.suffix.lower() == ".gif":
        with open(path, "rb") as f:
            gif_bytes = f.read()

        encoded = base64.b64encode(gif_bytes).decode("utf-8")

        st.markdown(
            f"""
            <div style="text-align:center;">
                <img
                    src="data:image/gif;base64,{encoded}"
                    style="width:100%; max-width:1500px; height:auto;"
                />
            </div>
            """,
            unsafe_allow_html=True,
        )

        if caption:
            st.caption(caption)
    else:
        st.image(
            str(path),
            caption=caption,
            use_container_width=True,
        )


def _select(label, values, formatter, key):
    values = [
        v for v in values
        if pd.notna(v) and str(v) not in {"", "None", "nan"}
    ]
    values = sorted(set(values), key=lambda x: formatter(x).lower())

    if not values:
        return None

    return st.selectbox(
        label,
        values,
        format_func=formatter,
        key=key,
    )


def visual_filters(df, key_prefix):
    work = df.copy()

    community = _select(
        "Community definition",
        work["community_family"].dropna().unique(),
        pretty_community,
        f"{key_prefix}_community",
    )
    if community:
        work = work[work["community_family"] == community]

    outcome = _select(
        "Outcome",
        work["outcome"].dropna().unique(),
        pretty_outcome,
        f"{key_prefix}_outcome",
    )
    if outcome:
        work = work[work["outcome"] == outcome]

    attack = _select(
        "Attack",
        work["attack_family"].dropna().unique(),
        pretty_attack,
        f"{key_prefix}_attack",
    )
    if attack:
        work = work[work["attack_family"] == attack]

    ranking = _select(
        "Ranking / subset criterion",
        work["ranking_metric"].dropna().unique(),
        pretty_ranking,
        f"{key_prefix}_ranking",
    )
    if ranking:
        work = work[work["ranking_metric"] == ranking]

    scale = None
    if work["scale"].notna().any():
        scale = _select(
            "View",
            work["scale"].dropna().unique(),
            pretty_scale,
            f"{key_prefix}_scale",
        )
        if scale:
            work = work[work["scale"] == scale]

    return work, {
        "community_family": community,
        "outcome": outcome,
        "attack_family": attack,
        "ranking_metric": ranking,
        "scale": scale,
    }


def selected_asset(work, key):
    if work is None or work.empty:
        return None

    if len(work) == 1:
        return work.iloc[0]

    idx = st.selectbox(
        "Figure",
        list(work.index),
        format_func=lambda i: work.loc[i, "filename"],
        key=key,
    )
    return work.loc[idx]


def show_table(df, preferred=None, height=330):
    if df is None or df.empty:
        st.info("No matching rows were found in the compact result table.")
        return

    view = df.copy()
    if preferred:
        cols = [c for c in preferred if c in view.columns]
        if cols:
            view = view[cols]

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        height=height,
    )


def download_dataframe(df, filename, label="Download CSV"):
    if df is None or df.empty:
        return

    st.download_button(
        label,
        df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )
