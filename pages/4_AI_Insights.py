"""Generate natural-language insights for a selected club using OpenAI."""

import streamlit as st
from utils.logger import logger

uploaded_files = st.session_state.get("uploaded_files", [])
if not uploaded_files:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

logger.info("📄 Page loaded: 4 AI Insights")

from utils.ai_feedback import generate_ai_summary

st.title("🧠 AI Insights")

if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.info("Please upload session files from the Home page.")
    st.stop()

df = st.session_state["session_df"]
club_list = sorted(df["Club"].dropna().unique())
selected_club = st.selectbox("Select a club for feedback", club_list)

if st.button("🧠 Generate AI Summary"):
    with st.spinner("Generating AI summary..."):
        feedback = generate_ai_summary(selected_club, df)
        sampled_df = df[df['Club'] == selected_club].sample(n=min(25, len(df[df['Club'] == selected_club])), random_state=42)
        feedback = generate_ai_summary(selected_club, sampled_df)
        st.session_state[f"ai_{selected_club}"] = feedback
        st.success("✅ Summary generated!")

# Show cached summary if it exists
cached = st.session_state.get(f"ai_{selected_club}")
if cached:
    st.markdown("### 💬 Summary")
    st.write(cached)
