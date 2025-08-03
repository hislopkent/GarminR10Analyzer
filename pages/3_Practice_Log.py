import streamlit as st
import pandas as pd
import os
from datetime import date

from utils.sidebar import render_sidebar
from utils.drill_recommendations import _DRILLS

st.set_page_config(layout="centered")
st.header("📝 Practice Log")

render_sidebar()

PRACTICE_LOG_FILE = "practice_log.csv"

# Prepare available drills from recommendations
AVAILABLE_DRILLS = [rec.drill for rec in _DRILLS.values()]

# Determine available clubs and sessions from uploaded data
df_all = st.session_state.get("df_all")
club_options = (
    sorted(df_all["Club"].dropna().unique())
    if df_all is not None and "Club" in df_all
    else []
)
session_options = (
    sorted(df_all["Session"].dropna().unique())
    if df_all is not None and "Session" in df_all
    else []
)

# Load existing practice log if available and ensure required columns
expected_cols = ["Date", "Club", "Session", "Notes", "Drills Completed"]
if os.path.exists(PRACTICE_LOG_FILE):
    log_df = pd.read_csv(PRACTICE_LOG_FILE)
    for col in expected_cols:
        if col not in log_df.columns:
            log_df[col] = ""
    log_df = log_df[expected_cols]
else:
    log_df = pd.DataFrame(columns=expected_cols)

st.subheader("Log a Practice Session")
if not club_options or not session_options:
    st.info("Upload session data to enable club and session selection.")
else:
    with st.form("practice_form"):
        session_date = st.date_input("Date", value=date.today())
        session_id = st.selectbox("Session", session_options)
        club = st.selectbox("Club", club_options)
        notes = st.text_area("Notes")
        st.markdown("#### Drills")
        drill_checks = {drill: st.checkbox(drill) for drill in AVAILABLE_DRILLS}
        submitted = st.form_submit_button("Save Session")

        if submitted:
            completed = [drill for drill, done in drill_checks.items() if done]
            new_row = {
                "Date": session_date.isoformat(),
                "Club": club,
                "Session": session_id,
                "Notes": notes,
                "Drills Completed": ", ".join(completed),
            }
            log_df = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
            try:
                log_df.to_csv(PRACTICE_LOG_FILE, index=False)
                st.success("Session saved")
            except Exception as e:
                st.error(f"Failed to save session: {e}")

if not log_df.empty:
    st.subheader("Practice History")
    session_filter = st.selectbox(
        "Filter by Session", ["All Sessions"] + sorted(log_df["Session"].dropna().unique())
    )
    if session_filter == "All Sessions":
        filtered_log = log_df
    else:
        filtered_log = log_df[log_df["Session"] == session_filter]
    st.dataframe(filtered_log, use_container_width=True)
    csv = filtered_log.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "practice_log.csv", "text/csv")
else:
    st.info("No practice sessions logged yet.")
