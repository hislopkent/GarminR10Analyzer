import streamlit as st
import pandas as pd
from utils.benchmarks import get_benchmarks

st.title("✅ Benchmark Comparison Report")

if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.info("Please upload session files from the Home page.")
    st.stop()

df = st.session_state["session_df"]
benchmarks = get_benchmarks()

def compare_to_benchmark(club, club_df):
    result = {"Club": club}
    club_stats = club_df.describe().T

    bmark = benchmarks.get(club)
    if not bmark:
        result["Note"] = "No benchmark available"
        return result

    for metric, target in bmark.items():
        if metric not in club_df.columns:
            continue
        value = club_df[metric].mean()
        if isinstance(target, tuple):
            result[metric] = "✅" if target[0] <= value <= target[1] else "❌"
        else:
            result[metric] = "✅" if value >= target else "❌"
    return result

results = []
for club in df["Club"].dropna().unique():
    club_df = df[df["Club"] == club]
    results.append(compare_to_benchmark(club, club_df))

st.subheader("Per-Club Benchmark Ratings")
st.dataframe(pd.DataFrame(results), use_container_width=True)
