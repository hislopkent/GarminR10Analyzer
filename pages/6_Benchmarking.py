"""Detailed club benchmarking page.

Allows users to select a club and optionally a session to review
shot-level dispersion and consistency statistics.  Visualisations help
identify patterns while coach-style feedback surfaces potential issues.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.logger import logger
from utils.data_utils import coerce_numeric

# Ensure data is loaded -----------------------------------------------------
if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.warning("\ud83d\udce4 Please upload CSV files on the home page first.")
    st.stop()

logger.info("\ud83d\udcc4 Page loaded: 6 Benchmarking")

st.title("\ud83d\udcc8 Club Benchmarking")

# Standardise column names --------------------------------------------------
col_map = {
    "Session Name": "session_name",
    "Club": "club",
    "Club Type": "club",
    "Carry Distance": "carry_distance",
    "Carry": "carry_distance",
    "Total Distance": "total_distance",
    "Ball Speed": "ball_speed",
    "Launch Angle": "launch_angle",
    "Backspin": "spin_rate",
    "Spin Rate": "spin_rate",
    "Apex Height": "apex_height",
    "Apex": "apex_height",
    "Side": "side_distance",
    "Side Distance": "side_distance",
    "Offline Distance": "offline_distance",
}
_df = st.session_state["session_df"].rename(
    columns={k: v for k, v in col_map.items() if k in st.session_state["session_df"].columns}
)
# ``rename`` can create duplicate columns when multiple source columns map to
# the same standardised name (e.g., "Carry" and "Carry Distance").  Remove
# duplicates so that subsequent ``df[col]`` lookups yield a Series.
_df = _df.loc[:, ~_df.columns.duplicated()]

required = [
    "club",
    "session_name",
    "carry_distance",
    "ball_speed",
    "launch_angle",
    "spin_rate",
    "offline_distance",
]
missing = [c for c in required if c not in _df.columns]
if missing:
    st.error("\u274c Missing required columns: " + ", ".join(missing))
    st.stop()

# Ensure numeric dtypes
for col in [
    "carry_distance",
    "total_distance",
    "ball_speed",
    "launch_angle",
    "spin_rate",
    "apex_height",
    "side_distance",
    "offline_distance",
]:
    if col in _df.columns:
        _df[col] = coerce_numeric(_df[col])

df = _df.dropna(subset=["club", "session_name"])

# Sidebar filters -----------------------------------------------------------
unique_clubs = sorted(df["club"].dropna().unique().tolist())
unique_sessions = sorted(df["session_name"].dropna().unique().tolist())

selected_club = st.sidebar.selectbox("Select Club", unique_clubs)
selected_session = st.sidebar.selectbox(
    "Select Session", options=["All Sessions"] + unique_sessions
)

# Data filtering
_df_club = df[df["club"] == selected_club]
if selected_session != "All Sessions":
    df_filtered = _df_club[_df_club["session_name"] == selected_session]
else:
    df_filtered = _df_club

if df_filtered.empty:
    st.info("No data for the selected filters.")
    st.stop()

st.markdown(
    f"## \ud83d\udccb Benchmarking: {selected_club}"
)
st.markdown(
    f"Showing data for **{len(df_filtered)} shots** "
    + ("(All Sessions)" if selected_session == "All Sessions" else f"from {selected_session}")
)

# Metrics summary -----------------------------------------------------------
metrics = df_filtered.agg(
    {
        "carry_distance": ["mean", "std"],
        "ball_speed": "mean",
        "launch_angle": "mean",
        "spin_rate": "mean",
        "offline_distance": ["mean", "std"],
        "apex_height": "mean",
    }
).T.reset_index()
metrics.columns = ["Metric", "Average", "Std Dev"]
metrics["Average"] = metrics["Average"].round(1)
metrics["Std Dev"] = metrics["Std Dev"].fillna("-").apply(
    lambda x: f"{x:.1f}" if isinstance(x, float) else x
)

st.dataframe(metrics, use_container_width=True)

# Carry distance histogram --------------------------------------------------
fig_hist = px.histogram(
    df_filtered,
    x="carry_distance",
    nbins=20,
    title=f"Carry Distance Distribution \u2013 {selected_club}",
    labels={"carry_distance": "Carry Distance (yds)"},
)
st.plotly_chart(fig_hist, use_container_width=True)

# Dispersion chart ----------------------------------------------------------
fig_disp = px.scatter(
    df_filtered,
    x="offline_distance",
    y="carry_distance",
    title=f"Dispersion Plot \u2013 {selected_club}",
    labels={
        "offline_distance": "Offline Distance (yds)",
        "carry_distance": "Carry Distance (yds)",
    },
    hover_data=["session_name"],
)
fig_disp.update_traces(
    marker=dict(size=8, opacity=0.7, line=dict(width=1, color="DarkSlateGrey"))
)
st.plotly_chart(fig_disp, use_container_width=True)

# Smart feedback ------------------------------------------------------------
st.markdown("## \ud83e\udde0 Coach’s Feedback")
carry_std = df_filtered["carry_distance"].std()
offline_std = df_filtered["offline_distance"].std()

if pd.notna(carry_std) and carry_std > 15:
    st.warning(
        "\u26a0\ufe0f High inconsistency in carry distance – consider working on strike location and tempo control."
    )
else:
    st.success("\u2705 Carry distance shows good consistency.")

if pd.notna(offline_std) and offline_std > 10:
    st.warning(
        "\u26a0\ufe0f Offline dispersion is wide – work on face angle or path to tighten dispersion."
    )
else:
    st.success("\u2705 Directional control appears solid.")
