import streamlit as st
import streamlit as st
import os
import pandas as pd
import numpy as np
import openai
import plotly.express as px
import plotly.graph_objects as go

from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

# Password protection
PASSWORD = os.environ.get("PASSWORD") or "demo123"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Protected App")
    password = st.text_input("Enter password:", type="password")
    if password == PASSWORD:
        st.session_state["authenticated"] = True
        st.experimental_rerun()
    elif password:
        st.error("❌ Incorrect password")
    st.stop()

# Logout button
if st.button("🔓 Logout"):
    st.session_state["authenticated"] = False
    st.experimental_rerun()

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

LOG_COLUMNS = ["Date", "Club", "Session", "Notes", "Drills Completed"]

# Load existing practice log if available
if os.path.exists(PRACTICE_LOG_FILE):
    try:
        log_df = pd.read_csv(PRACTICE_LOG_FILE)
    except Exception as e:
        st.error(f"Failed to load practice log: {e}")
        try:
            with open(
                PRACTICE_LOG_FILE, "r", encoding="utf-8", errors="replace"
            ) as f:
                preview_lines = [next(f, "") for _ in range(10)]
            preview_text = "".join(preview_lines)
            st.text("First 10 lines of the practice log file:")
            st.code(preview_text)
        except Exception:
            pass
        log_df = pd.DataFrame(columns=LOG_COLUMNS)
else:
    log_df = pd.DataFrame(columns=LOG_COLUMNS)

# Ensure required columns exist (for backward compatibility)
for col in LOG_COLUMNS:
    if col not in log_df.columns:
        log_df[col] = ""
log_df = log_df[LOG_COLUMNS]

st.subheader("Log a Practice Session")
with st.form("practice_form"):
    session_date = st.date_input("Date", value=date.today())

    # Dropdowns for club and session ID
    df_all = st.session_state.get("df_all")
    club_options = []
    session_options = []
    if isinstance(df_all, pd.DataFrame) and not df_all.empty:
        if "Club" in df_all.columns:
            club_options = sorted(df_all["Club"].dropna().unique())
        if "Session" in df_all.columns:
            session_options = sorted(df_all["Session"].dropna().unique())
    if not club_options:
        club_options = sorted(log_df["Club"].dropna().unique())
    if not session_options:
        session_options = sorted(log_df["Session"].dropna().unique())
    club = (
        st.selectbox("Club", club_options)
        if club_options
        else st.text_input("Club")
    )
    session_id = (
        st.selectbox("Session", session_options)
        if session_options
        else st.text_input("Session")
    )

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
    filter_options = ["All"] + sorted(log_df["Session"].dropna().unique().tolist())
    session_filter = st.selectbox("Filter by Session", filter_options)
    display_df = (
        log_df if session_filter == "All" else log_df[log_df["Session"] == session_filter]
    )
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "practice_log.csv", "text/csv")
else:
    st.info("No practice sessions logged yet.")
