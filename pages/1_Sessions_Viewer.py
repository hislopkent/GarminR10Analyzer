"""Table-based view of all uploaded Garmin sessions.

This page provides a simple table of all processed shots so that users can
inspect individual rows.  It is intentionally minimal; heavy analysis and
visualisation live on other pages.  The sidebar provides navigation links
and contextual guidance.
"""

import streamlit as st
from utils.logger import logger

uploaded_files = st.session_state.get("uploaded_files", [])
if not uploaded_files:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

logger.info("📄 Page loaded: 1 Sessions Viewer")

import os
import pandas as pd
import numpy as np
import openai
import plotly.express as px
import plotly.graph_objects as go

from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

# Password protection

from utils.sidebar import render_sidebar

st.set_page_config(layout="centered")
st.header("📋 Sessions Viewer")

# CSS for compact tables
st.markdown(
    """
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
        .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
        .sidebar a {color: #2ca02c; text-decoration: none;}
        .sidebar a:hover {background-color: #228B22; text-decoration: underline;}
    </style>
""",
    unsafe_allow_html=True,
)

render_sidebar()

# Conditional guidance
if "df_all" not in st.session_state or st.session_state["df_all"].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get("df_all")

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    # Sidebar options to select which session(s) to display
    df = df_all.copy()
    session_names = df["Session Name"].dropna().unique().tolist()
    st.sidebar.markdown("### Session View")
    view_option = st.sidebar.selectbox(
        "Choose sessions to display",
        ["Latest Session", "Last 5 Sessions Combined", "Select Sessions"],
    )

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    if view_option == "Latest Session":
        if "Date" in df.columns and df["Date"].notna().any():
            latest_session = df.loc[df["Date"].idxmax(), "Session Name"]
        else:
            latest_session = session_names[-1]
        df_view = df[df["Session Name"] == latest_session]
    elif view_option == "Last 5 Sessions Combined":
        if "Date" in df.columns and df["Date"].notna().any():
            session_order = (
                df.drop_duplicates("Session Name").sort_values("Date")
            )["Session Name"].tolist()
        else:
            session_order = session_names
        last_sessions = session_order[-5:]
        df_view = df[df["Session Name"].isin(last_sessions)]
    else:  # Select Sessions
        chosen = st.sidebar.multiselect("Select session(s)", session_names)
        df_view = df[df["Session Name"].isin(chosen)] if chosen else df.iloc[0:0]

    st.subheader("Processed Data")
    st.dataframe(df_view, use_container_width=True)
    if df_view.empty:
        st.info("No sessions selected.")
    st.info(
        "Explore the shots above. Navigate to Home for uploads or Dashboard for summaries."
    )
