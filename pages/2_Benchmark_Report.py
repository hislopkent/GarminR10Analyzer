import streamlit as st
import pandas as pd
from utils.benchmarks import check_benchmark

from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

st.set_page_config(layout="centered")
st.header("📌 Benchmark Report – Club Performance vs. Goals")

render_sidebar()

if "df_all" not in st.session_state or st.session_state["df_all"].empty:
    st.warning("No session data found. Please upload data on the Home page.")
else:
    df_all = st.session_state["df_all"].copy()
    numeric_cols = [
        "Carry",
        "Backspin",
        "Sidespin",
        "Total",
        "Smash Factor",
        "Apex Height",
        "Launch Angle",
        "Attack Angle",
    ]

    for col in numeric_cols:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors="coerce")
    df_all = df_all.dropna(subset=["Club"] + numeric_cols, how="any")

    sessions = st.multiselect("Select Sessions", df_all["Session"].unique(), default=df_all["Session"].unique())
    clubs = st.multiselect("Select Clubs", df_all["Club"].unique(), default=df_all["Club"].unique())
    filtered = df_all[df_all["Session"].isin(sessions) & df_all["Club"].isin(clubs)]

    if filtered.empty:
        st.info("No data found with the current filters.")
    else:
        st.subheader("✅ Benchmark Comparison Results")
        show_ai_feedback = st.checkbox("\U0001F4A1 Show AI Summary Under Each Club", value=False)
        if show_ai_feedback:
            st.info("Generating personalized feedback per club based on your session data...")

        grouped = filtered.groupby("Club")[numeric_cols].mean().round(1).reset_index()

        cols = st.columns(3)
        for idx, row in grouped.iterrows():
            with cols[idx % 3]:
                club_name = row["Club"]
                st.markdown(f"### {club_name}")
                result_lines = check_benchmark(club_name, row)
                for line in result_lines:
                    st.write(f"- {line}")
                if show_ai_feedback:
                    with st.spinner(f"Analyzing {club_name}..."):
                        feedback = generate_ai_summary(club_name, filtered)
                        st.markdown(f"**AI Feedback:**\n\n> {feedback}")

        st.markdown("---")
        st.markdown(
            "This report compares your club performance against Jon Sherman–inspired benchmarks for mid-handicap players. Use ✅ and ❌ to focus your practice on key weaknesses."
        )
