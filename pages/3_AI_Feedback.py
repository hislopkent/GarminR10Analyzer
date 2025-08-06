"""Consolidated AI insights and practice summaries."""

import json
import os

import streamlit as st
import pandas as pd

from utils.logger import logger
from utils.data_utils import coerce_numeric
from utils.ai_feedback import generate_ai_summary, generate_ai_batch_summaries
from utils.practice_ai import analyze_practice_session
from utils.drill_recommendations import recommend_drills
from utils.page_utils import require_data
from utils.responsive import configure_page

logger.info("📄 Page loaded: AI Feedback")
configure_page()
st.title("🧠 AI Feedback")

AI_CACHE_PATH = os.path.join("sample_data", "ai_cache.json")


def _load_ai_cache() -> dict:
    if os.path.exists(AI_CACHE_PATH):
        try:
            with open(AI_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):  # pragma: no cover - rare
            return {}
    return {}


def _save_ai_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(AI_CACHE_PATH), exist_ok=True)
    with open(AI_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)


ai_cache = _load_ai_cache()

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

uploaded_sessions = st.session_state.get("uploaded_sessions", [])
if set(st.session_state.get("ai_sessions_snapshot", [])) != set(uploaded_sessions):
    st.info("📥 New session files detected. Updating summaries...")
    st.session_state["practice_summary"] = []
    for key in list(st.session_state.keys()):
        if key.startswith("ai_"):
            del st.session_state[key]
    st.session_state["ai_sessions_snapshot"] = uploaded_sessions

drill_map = recommend_drills(df)

insight_tab, session_tab = st.tabs(["Club Insight", "Practice Summary"])

with insight_tab:
    club_list = sorted(df["Club"].dropna().unique())
    if not club_list:
        st.info("No club data available.")
    else:
        auto = st.checkbox("Auto-generate on club selection", key="auto_summary")
        selected_club = st.selectbox("Select a club for feedback", club_list)

        def _run_club_summary():
            with st.spinner("Generating AI summary..."):
                sampled = df[df["Club"] == selected_club].sample(
                    n=min(25, len(df[df["Club"] == selected_club])), random_state=42
                )
                summary, stats = generate_ai_summary(selected_club, sampled)
                st.session_state[f"ai_{selected_club}"] = {
                    "summary": summary,
                    "stats": stats,
                }
                ai_cache[selected_club] = {
                    "sessions": uploaded_sessions,
                    "summary": summary,
                    "stats": stats,
                }
                _save_ai_cache(ai_cache)
                st.session_state["ai_sessions_snapshot"] = uploaded_sessions
                st.success("✅ Summary generated!")

        if st.button("Generate Summary"):
            _run_club_summary()
        prev_club = st.session_state.get("_prev_club")
        if auto and prev_club != selected_club:
            _run_club_summary()
        st.session_state["_prev_club"] = selected_club

        cached = st.session_state.get(f"ai_{selected_club}")
        if not cached:
            disk_cached = ai_cache.get(selected_club)
            if disk_cached and disk_cached.get("sessions", disk_cached.get("files")) == uploaded_sessions:
                st.session_state[f"ai_{selected_club}"] = disk_cached
                cached = disk_cached
        if cached:
            st.markdown("### 💬 Summary")
            st.write(cached["summary"])
            st.markdown("**Stats Used:**")
            st.table(pd.DataFrame([cached["stats"]]))
            drills = drill_map.get(selected_club, [])
            if drills:
                st.markdown("### 🏌️‍♂️ Recommended Drills")
                for rec in drills:
                    st.write(f"- {rec.drill}")

with session_tab:
    if st.button("Generate Practice Summary"):
        with st.spinner("Analyzing practice session..."):
            base_stats = analyze_practice_session(df, with_summary=False)
            summaries = generate_ai_batch_summaries(df)
            for entry in base_stats:
                club = entry["club"]
                if club in summaries:
                    entry["summary"] = summaries[club]["summary"]
                    entry["stats"] = summaries[club]["stats"]
            st.session_state["practice_summary"] = base_stats
            st.session_state["ai_sessions_snapshot"] = uploaded_sessions
            st.success("✅ Summary generated!")
    results = st.session_state.get("practice_summary", [])
    for entry in results:
        st.subheader(f"📌 {entry['club']}")
        if entry.get("stats"):
            st.markdown("**Stats Used:**")
            st.table(pd.DataFrame([entry["stats"]]))
        st.markdown("**AI Summary:**")
        st.info(entry.get("summary", ""))
        if entry["issues"]:
            st.markdown("**Detected Issues:**")
            for issue in entry["issues"]:
                st.write(f"- {issue}")
        drills = drill_map.get(entry["club"], [])
        if drills:
            st.markdown("**Recommended Drills:**")
            for rec in drills:
                st.write(f"- {rec.drill}")
        st.markdown("---")
