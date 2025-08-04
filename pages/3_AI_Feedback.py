"""Consolidated AI insights and practice summaries."""

import streamlit as st

from utils.logger import logger
from utils.data_utils import coerce_numeric
from utils.ai_feedback import generate_ai_summary
from utils.practice_ai import analyze_practice_session
from utils.page_utils import require_data
from utils.responsive import configure_page

logger.info("📄 Page loaded: AI Feedback")
configure_page()
st.title("🧠 AI Feedback")

df = require_data().copy()
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
        df[col] = coerce_numeric(df[col])

insight_tab, session_tab = st.tabs(["Club Insight", "Practice Summary"])

with insight_tab:
    club_list = sorted(df["Club"].dropna().unique())
    selected_club = st.selectbox("Select a club for feedback", club_list)
    if st.button("Generate Summary"):
        with st.spinner("Generating AI summary..."):
            sampled = df[df["Club"] == selected_club].sample(
                n=min(25, len(df[df["Club"] == selected_club])), random_state=42
            )
            feedback = generate_ai_summary(selected_club, sampled)
            st.session_state[f"ai_{selected_club}"] = feedback
            st.success("✅ Summary generated!")
    cached = st.session_state.get(f"ai_{selected_club}")
    if cached:
        st.markdown("### 💬 Summary")
        st.write(cached)

with session_tab:
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
