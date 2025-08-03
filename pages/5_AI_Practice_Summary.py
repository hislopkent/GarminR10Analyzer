import streamlit as st
from utils.logger import logger
uploaded_files = st.session_state.get("uploaded_files", [])
if not uploaded_files:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

import pandas as pd
from utils.session_loader import load_sessions
from utils.practice_ai import analyze_practice_session
from utils.logger import logger

st.title("🧠 AI Practice Summary")

uploaded_files = st.file_uploader("Upload Garmin CSV file(s)", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    df = load_sessions(uploaded_files)

    if df is not None and not df.empty:
        logger.info("Analyzing session with AI practice engine")
        results = analyze_practice_session(df)

        for entry in results:
            st.subheader(f"📌 {entry['club']}")
            st.markdown("**AI Summary:**")
            st.info(entry["summary"])
            if entry["issues"]:
                st.markdown("**Detected Issues:**")
                for issue in entry["issues"]:
                    st.write(f"- {issue}")
            st.markdown("---")
    else:
        st.error("⚠️ Unable to parse data from uploaded file(s).")
else:
    st.warning("📤 Upload one or more Garmin CSV files to begin.")
