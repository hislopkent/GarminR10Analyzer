import streamlit as st
import pandas as pd
from datetime import datetime

st.title("📝 Practice Log")

# Initialize log in session_state
if "practice_log" not in st.session_state:
    st.session_state.practice_log = []

# Input form
with st.form("log_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.today())
    focus_area = st.selectbox("Primary Focus", ["Driving", "Approach", "Short Game", "Putting", "Recovery", "Other"])
    notes = st.text_area("Session Notes or Drills")
    submitted = st.form_submit_button("Add to Log")

    if submitted:
        st.session_state.practice_log.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Focus": focus_area,
            "Notes": notes
        })
        st.success("✅ Entry added.")

# Display the log
if st.session_state.practice_log:
    st.subheader("📅 Your Practice History")
    df_log = pd.DataFrame(st.session_state.practice_log)
    st.dataframe(df_log, use_container_width=True)

    csv = df_log.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Log as CSV", data=csv, file_name="practice_log.csv", mime="text/csv")
else:
    st.info("No entries yet. Use the form above to log your first practice session.")
