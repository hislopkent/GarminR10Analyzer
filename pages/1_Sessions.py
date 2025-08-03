"""Session viewer and practice log consolidated into a single page."""

import pandas as pd
import streamlit as st

from datetime import datetime

from utils.logger import logger
from utils.page_utils import require_data

logger.info("📄 Page loaded: Sessions")
st.title("📋 Sessions")

df_all = require_data().copy()

viewer_tab, log_tab = st.tabs(["Viewer", "Practice Log"])

with viewer_tab:
    st.subheader("Session Data")
    session_names = df_all["Session Name"].dropna().unique().tolist()
    view_option = st.selectbox(
        "Choose sessions to display",
        ["Latest Session", "Last 5 Sessions", "Select Sessions"],
    )

    if "Date" in df_all.columns:
        df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")

    if view_option == "Latest Session":
        if "Date" in df_all.columns and df_all["Date"].notna().any():
            latest_session = df_all.loc[df_all["Date"].idxmax(), "Session Name"]
        else:
            latest_session = session_names[-1]
        df_view = df_all[df_all["Session Name"] == latest_session]
    elif view_option == "Last 5 Sessions":
        if "Date" in df_all.columns and df_all["Date"].notna().any():
            session_order = (
                df_all.drop_duplicates("Session Name").sort_values("Date")
            )["Session Name"].tolist()
        else:
            session_order = session_names
        last_sessions = session_order[-5:]
        df_view = df_all[df_all["Session Name"].isin(last_sessions)]
    else:  # Select Sessions
        chosen = st.multiselect("Select session(s)", session_names)
        df_view = (
            df_all[df_all["Session Name"].isin(chosen)] if chosen else df_all.iloc[0:0]
        )

    st.dataframe(df_view, use_container_width=True)
    if df_view.empty:
        st.info("No sessions selected.")

with log_tab:
    st.subheader("Practice Log")
    if "practice_log" not in st.session_state:
        st.session_state.practice_log = []

    with st.form("log_form", clear_on_submit=True):
        date = st.date_input("Date", value=datetime.today())
        focus_area = st.selectbox(
            "Primary Focus",
            ["Driving", "Approach", "Short Game", "Putting", "Recovery", "Other"],
        )
        notes = st.text_area("Session Notes or Drills")
        submitted = st.form_submit_button("Add to Log")
        if submitted:
            st.session_state.practice_log.append(
                {"Date": date.strftime("%Y-%m-%d"), "Focus": focus_area, "Notes": notes}
            )
            st.success("✅ Entry added.")

    if st.session_state.practice_log:
        st.markdown("### 📅 Your Practice History")
        df_log = pd.DataFrame(st.session_state.practice_log)
        st.dataframe(df_log, use_container_width=True)
        csv = df_log.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Log as CSV",
            data=csv,
            file_name="practice_log.csv",
            mime="text/csv",
        )
    else:
        st.info("No entries yet. Use the form above to log your first practice session.")
