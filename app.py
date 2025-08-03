import streamlit as st
import pandas as pd
import numpy as np
import os
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")

render_sidebar()
st.title("Garmin R10 Multi-Session Analyzer")
from utils.session_loader import load_sessions

# --- File Upload ---
uploaded_files = st.file_uploader('Upload Garmin R10 CSV files', type='csv', accept_multiple_files=True)
st.warning('⚠️ Uploads over 100MB may fail on free hosting tiers like Render Starter Plan.')

# Validate and summarize uploaded data
valid_files = []
for file in uploaded_files:
    if file.size > 100 * 1024 * 1024:  # 100MB
        st.error(f"{file.name} is too large (>100MB). Please upload a smaller file.")
    else:
        valid_files.append(file)

if valid_files:
    session_df = load_sessions(valid_files)
    st.session_state["session_df"] = session_df

    st.success(f"Loaded {len(session_df)} shots from {len(valid_files)} sessions.")
    st.dataframe(session_df.head(1000), use_container_width=True)
else:
    st.stop()
if uploaded_files:
    session_df = load_sessions(uploaded_files)
    st.session_state["session_df"] = session_df
    st.success(f"Loaded {len(session_df)} shots from {len(uploaded_files)} sessions.")
    st.dataframe(session_df.head(), use_container_width=True)
st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")
