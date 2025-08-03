import streamlit as st
from utils.ai_feedback import generate_ai_summary

st.title("🧠 AI Insights")

if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.info("Please upload session files from the Home page.")
    st.stop()

df = st.session_state["session_df"]
club_list = sorted(df["Club"].dropna().unique())
selected_club = st.selectbox("Select a club for feedback", club_list)

with st.spinner("Generating AI summary..."):
    feedback = generate_ai_summary(selected_club, df)
    st.markdown("### 💬 Summary")
    st.write(feedback)
