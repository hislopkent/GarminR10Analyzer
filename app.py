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
if uploaded_files:
    session_df = load_sessions(uploaded_files)
    st.session_state["session_df"] = session_df
    st.success(f"Loaded {len(session_df)} shots from {len(uploaded_files)} sessions.")
    st.dataframe(session_df.head(), use_container_width=True)
st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")
