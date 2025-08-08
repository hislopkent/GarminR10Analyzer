"""Minimal Streamlit application for uploading Garmin R10 CSV files."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.session_loader import load_sessions

# Basic page configuration
st.set_page_config(page_title="Garmin R10 Analyzer")
st.title("\U0001F4CA Garmin R10 Analyzer")

# Ensure a dataframe is always available in session state
if "session_df" not in st.session_state:
    st.session_state["session_df"] = pd.DataFrame()

# File uploader allowing multiple CSVs
uploaded_files = st.file_uploader(
    "Upload one or more Garmin CSV files",
    type=["csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    df_new = load_sessions(uploaded_files)
    if not df_new.empty:
        if st.session_state["session_df"].empty:
            st.session_state["session_df"] = df_new
        else:
            st.session_state["session_df"] = pd.concat(
                [st.session_state["session_df"], df_new], ignore_index=True
            )
        st.success(
            f"Loaded {len(df_new['Session Name'].drop_duplicates())} session(s). Navigate using the sidebar."
        )

# Display a list of sessions currently stored
if not st.session_state["session_df"].empty:
    sessions = st.session_state["session_df"]["Session Name"].drop_duplicates().tolist()
    st.write("Current sessions:", sessions)
else:
    st.info("No sessions uploaded yet.")
