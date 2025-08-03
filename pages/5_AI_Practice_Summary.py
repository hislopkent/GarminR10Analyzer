"""Summarise an entire practice session with AI-derived feedback."""

import streamlit as st
from utils.logger import logger

uploaded_files = st.session_state.get("uploaded_files", [])
if not uploaded_files:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

from utils.practice_ai import analyze_practice_session

st.title("🧠 AI Practice Summary")

df = st.session_state.get("session_df")

if df is not None and not df.empty:
    df = df.copy()
    for col in [
        "Carry Distance",
        "Carry",
        "Smash Factor",
        "Launch Angle",
        "Backspin",
        "Spin Rate",
        "Offline",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
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
