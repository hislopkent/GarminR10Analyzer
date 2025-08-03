"""High-level club performance dashboard.

This page summarises a golfer's performance across all clubs. Users can
select a session, review averages and consistency per club, and view quick
visualisations. Coach-style notes highlight potential red flags.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.logger import logger

# Ensure session data is available
if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

logger.info("📄 Page loaded: 0 Dashboard")

st.title("📊 Club Performance Summary")

# Copy and standardise column names
_df = st.session_state["session_df"].copy()
col_map = {
    "Session Name": "session_name",
    "Club": "club",
    "Club Type": "club",
    "Carry Distance": "carry_distance",
    "Carry": "carry_distance",
    "Ball Speed": "ball_speed",
    "Launch Angle": "launch_angle",
    "Backspin": "spin_rate",
    "Spin Rate": "spin_rate",
}
_df = _df.rename(columns={k: v for k, v in col_map.items() if k in _df.columns})

required_cols = [
    "session_name",
    "club",
    "carry_distance",
    "ball_speed",
    "launch_angle",
    "spin_rate",
]
missing = [c for c in required_cols if c not in _df.columns]
if missing:
    st.error("❌ Missing required columns: " + ", ".join(missing))
    st.stop()

# Convert numeric columns
for col in ["carry_distance", "ball_speed", "launch_angle", "spin_rate"]:
    _df[col] = pd.to_numeric(_df[col], errors="coerce")

df = _df

# Step 1: Add session selection dropdown
sessions = df["session_name"].dropna().unique().tolist()
selected_session = st.selectbox("Select Session", options=["All Sessions"] + sessions)
df_filtered = df if selected_session == "All Sessions" else df[df["session_name"] == selected_session]

# Step 2: Create a club summary table
club_summary = df_filtered.groupby("club").agg(
    total_shots=("carry_distance", "count"),
    avg_carry=("carry_distance", "mean"),
    std_carry=("carry_distance", "std"),
    avg_ball_speed=("ball_speed", "mean"),
    avg_launch_angle=("launch_angle", "mean"),
    avg_spin_rate=("spin_rate", "mean"),
).reset_index()

st.markdown("## 🏌️‍♂️ Club Performance Summary")
st.dataframe(
    club_summary.style.format(
        {
            "avg_carry": "{:.1f}",
            "std_carry": "{:.1f}",
            "avg_ball_speed": "{:.1f}",
            "avg_launch_angle": "{:.1f}",
            "avg_spin_rate": "{:.0f}",
        }
    )
)

# Step 3: Add a bar chart of average carry distance per club
fig_carry = px.bar(
    club_summary,
    x="club",
    y="avg_carry",
    text="avg_carry",
    title="Average Carry Distance by Club",
    labels={"avg_carry": "Avg Carry (yds)", "club": "Club"},
)
fig_carry.update_traces(texttemplate="%{text:.1f}", textposition="outside")
st.plotly_chart(fig_carry, use_container_width=True)

# Step 4: Add a pie chart for shot usage by club
fig_pie = px.pie(
    club_summary,
    values="total_shots",
    names="club",
    title="Shot Volume by Club",
)
st.plotly_chart(fig_pie, use_container_width=True)

# Step 5: Add red flag section for high variability clubs
st.markdown("## ⚠️ Inconsistency Warning")
high_variability = club_summary.sort_values("std_carry", ascending=False).head(3)
st.dataframe(high_variability[["club", "std_carry"]].style.format("{:.1f}"))

# Step 6: Add basic coach-style feedback
st.markdown("## 📊 Coach’s Notes")
for _, row in club_summary.iterrows():
    if row["std_carry"] > 15:
        st.write(
            f"🟡 Your **{row['club']}** has a high carry distance variance ({row['std_carry']:.1f} yds). "
            "Consider strike pattern drills or better clubface control."
        )
    if row["avg_carry"] < 100 and "wedge" in str(row["club"]).lower():
        st.write(
            f"⚠️ Your **{row['club']}** carry is lower than expected. "
            "Check contact quality and ball-first strike."
        )

# Optional: Add expanders for each club with descriptive stats
for club, club_df in df_filtered.groupby("club"):
    with st.expander(f"{club} details"):
        st.write(club_df[["carry_distance", "ball_speed", "launch_angle", "spin_rate"]].describe())
