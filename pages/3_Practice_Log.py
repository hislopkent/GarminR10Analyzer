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
        log_df = pd.DataFrame(columns=["Date", "Notes", "Drills Completed"])
else:
    log_df = pd.DataFrame(columns=["Date", "Notes", "Drills Completed"])

st.subheader("Log a Practice Session")
with st.form("practice_form"):
    session_date = st.date_input("Date", value=date.today())
    notes = st.text_area("Notes")
    st.markdown("#### Drills")
    drill_checks = {drill: st.checkbox(drill) for drill in AVAILABLE_DRILLS}
    submitted = st.form_submit_button("Save Session")

    if submitted:
        completed = [drill for drill, done in drill_checks.items() if done]
        new_row = {
            "Date": session_date.isoformat(),
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
    st.dataframe(log_df, use_container_width=True)
    csv = log_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "practice_log.csv", "text/csv")
else:
    st.info("No practice sessions logged yet.")
