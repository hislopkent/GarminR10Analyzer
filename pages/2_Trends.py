"""Trend and progression analysis page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.page_utils import require_data
from utils.responsive import configure_page
from utils.data_utils import classify_shots

configure_page()
st.title("📉 Trends")

df = require_data().copy()
if df.empty:
    st.info("Upload session data to view trends.")
    st.stop()

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

df = classify_shots(df)
use_quality = st.checkbox(
    "Include only 'good' shots",
    value=True,
    help="Keep shots labelled as 'good' and ignore ones tagged 'miss' or 'outlier'",
)
if use_quality and "Quality" in df.columns:
    df = df[df["Quality"] == "good"]

if df.empty:
    st.info("No data available after filtering.")
    st.stop()

summary = (
    df.groupby(["Session Name", "Club"])["Carry Distance"].mean().reset_index()
)

club_options = sorted(summary["Club"].dropna().unique())
if not club_options:
    st.info("No club data available.")
    st.stop()
selected_club = st.selectbox("Select club", club_options)
club_df = summary[summary["Club"] == selected_club].copy()

if "Date" in df.columns:
    order = (
        df.drop_duplicates("Session Name")
        .sort_values("Date")
        ["Session Name"]
        .tolist()
    )
    club_df["Session Name"] = pd.Categorical(
        club_df["Session Name"], categories=order, ordered=True
    )
    club_df = club_df.sort_values("Session Name")

fig = px.line(
    club_df,
    x="Session Name",
    y="Carry Distance",
    markers=True,
    title=f"Average Carry Trend – {selected_club}",
)
st.plotly_chart(fig, use_container_width=True)

window = st.slider("Rolling window", 1, 5, 3)
if len(club_df) >= window:
    club_df["Rolling"] = club_df["Carry Distance"].rolling(window).mean()
    fig_roll = px.line(
        club_df,
        x="Session Name",
        y="Rolling",
        markers=True,
        title=f"{selected_club} {window}-session rolling average",
    )
    st.plotly_chart(fig_roll, use_container_width=True)
