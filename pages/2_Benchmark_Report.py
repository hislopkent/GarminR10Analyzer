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


from utils.benchmarks import check_benchmark
from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_batch_summaries


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

    sessions = st.multiselect(
        "Select Sessions", df_all["Session"].unique(), default=df_all["Session"].unique()
    )
    clubs = st.multiselect(
        "Select Clubs", df_all["Club"].unique(), default=df_all["Club"].unique()
    )
    filtered = df_all[df_all["Session"].isin(sessions) & df_all["Club"].isin(clubs)]

    if filtered.empty:
        st.info("No data found with the current filters.")
    else:
        st.subheader("✅ Benchmark Comparison Results")

        # store AI summaries between reruns
        st.session_state.setdefault("club_summaries", {})

        grouped = (
            filtered.groupby("Club")[numeric_cols].mean().round(1).reset_index()
        )

        generate_clicked = st.button("Generate All Feedback")

        @st.cache_data
        def build_benchmark_table(grouped_df):
            records = []
            for _, row in grouped_df.iterrows():
                club = row["Club"]
                lines = check_benchmark(club, row)
                record = {"Club": club}
                for line in lines:
                    if ": " not in line:
                        continue
                    metric, result = line.split(": ", 1)
                    record[metric] = result
                records.append(record)
            return pd.DataFrame(records).set_index("Club")

        table_df = build_benchmark_table(grouped)

        def color_result(val):
            if isinstance(val, str):
                if val.startswith("✅"):
                    return "background-color:#d4edda"
                if val.startswith("❌"):
                    return "background-color:#f8d7da"
            return ""

        st.dataframe(
            table_df.style.applymap(color_result), use_container_width=True
        )

        if generate_clicked:
            missing = [
                club
                for club in grouped["Club"]
                if club not in st.session_state["club_summaries"]
            ]
            if missing:
                with st.spinner("Analyzing clubs..."):
                    feedback_map = generate_ai_batch_summaries(
                        filtered[filtered["Club"].isin(missing)]
                    )
                for club in missing:
                    with st.spinner(f"Analyzing {club}..."):
                        st.session_state["club_summaries"][club] = feedback_map.get(
                            club, "⚠️ No feedback available."
                        )

        for club in grouped["Club"]:
            with st.expander(f"🧠 {club} Feedback"):
                feedback = st.session_state["club_summaries"].get(club)
                if feedback:
                    st.write(feedback)
                else:
                    st.write("Click 'Generate All Feedback' to see AI insights.")

        if st.session_state["club_summaries"]:
            try:
                table_md = table_df.to_markdown()
            except Exception:
                table_md = table_df.to_csv()
            sections = ["# Benchmark Report", table_md]
            for club, fb in st.session_state["club_summaries"].items():
                sections.append(f"## {club} Feedback\n{fb}")
            report_md = "\n\n".join(sections)
            st.download_button(
                "Download Report", report_md, file_name="benchmark_report.md"
            )

        st.markdown("---")
        st.markdown(
            "This report compares your club performance against Jon Sherman–inspired benchmarks for mid-handicap players. Use ✅ and ❌ to focus your practice on key weaknesses."
        )
