"""Benchmark comparison page.

For each club, this page compares the user's averages against a set of
hand-crafted benchmarks inspired by Jon Sherman's practice philosophy. The
output is a simple table of ✅/❌ ratings to highlight areas that may need
attention.
"""

import pandas as pd
import streamlit as st

from utils.logger import logger
from utils.benchmarks import get_benchmarks
from utils.data_utils import coerce_numeric
from utils.page_utils import require_data

logger.info("📄 Page loaded: Benchmark Report")

st.title("✅ Benchmark Comparison Report")

df = require_data()
club_data = {club: grp for club, grp in df.groupby("Club")}
benchmarks = get_benchmarks()

def compare_to_benchmark(club, club_df):
    result = {"Club": club}

    bmark = benchmarks.get(club)
    if not bmark:
        result["Note"] = "No benchmark available"
        return result

    club_df = club_df.copy()
    for col in ["Carry Distance", "Carry", "Smash Factor", "Launch Angle", "Backspin"]:
        if col in club_df.columns:
            club_df[col] = coerce_numeric(club_df[col])

    for metric, target in bmark.items():
        col = metric
        if col not in club_df.columns:
            if metric == "Carry" and "Carry Distance" in club_df.columns:
                col = "Carry Distance"
            else:
                continue
        value = club_df[col].mean()
        if isinstance(target, tuple):
            result[metric] = "✅" if target[0] <= value <= target[1] else "❌"
        else:
            result[metric] = "✅" if value >= target else "❌"
    return result

results = []
for club in club_data:
    club_df = club_data[club]
    results.append(compare_to_benchmark(club, club_df))

st.subheader("Per-Club Benchmark Ratings")
st.dataframe(pd.DataFrame(results), use_container_width=True)
