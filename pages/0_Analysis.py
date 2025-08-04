"""Combined dashboard and benchmarking analysis page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.logger import logger
from utils.data_utils import coerce_numeric
from utils.page_utils import require_data
from utils.responsive import configure_page

logger.info("📄 Page loaded: Analysis")
configure_page()
st.title("📈 Analysis")

# Load and standardise data -------------------------------------------------
raw_df = require_data().copy()
col_map = {
    "Session Name": "session_name",
    "Club": "club",
    "Club Type": "club",
    "Carry Distance": "carry_distance",
    "Carry": "carry_distance",
    "Total Distance": "total_distance",
    "Ball Speed": "ball_speed",
    "Launch Angle": "launch_angle",
    "Backspin": "spin_rate",
    "Spin Rate": "spin_rate",
    "Apex Height": "apex_height",
    "Apex": "apex_height",
    "Side": "side_distance",
    "Side Distance": "side_distance",
    "Offline Distance": "offline_distance",
    "Offline": "offline_distance",
}

df = raw_df.rename(columns={k: v for k, v in col_map.items() if k in raw_df.columns})
# ``rename`` may create duplicate columns when multiple source names map to the
# same target. Remove duplicates so downstream selections return Series objects.
df = df.loc[:, ~df.columns.duplicated()]

for col in [
    "carry_distance",
    "total_distance",
    "ball_speed",
    "launch_angle",
    "spin_rate",
    "apex_height",
    "side_distance",
    "offline_distance",
]:
    if col in df.columns:
        df[col] = coerce_numeric(df[col])

overview_tab, benchmark_tab = st.tabs(["Overview", "Benchmarking"])

# ---------------------------------------------------------------------------
with overview_tab:
    st.subheader("Club Performance Overview")

    sessions = df["session_name"].dropna().unique().tolist()
    selected_session = st.selectbox(
        "Select Session", options=["All Sessions"] + sessions
    )
    df_filtered = (
        df if selected_session == "All Sessions" else df[df["session_name"] == selected_session]
    )

    club_summary = df_filtered.groupby("club").agg(
        total_shots=("carry_distance", "count"),
        avg_carry=("carry_distance", "mean"),
        std_carry=("carry_distance", "std"),
        avg_ball_speed=("ball_speed", "mean"),
        avg_launch_angle=("launch_angle", "mean"),
        avg_spin_rate=("spin_rate", "mean"),
    ).reset_index()

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

    fig_pie = px.pie(
        club_summary,
        values="total_shots",
        names="club",
        title="Shot Volume by Club",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("## ⚠️ Inconsistency Warning")
    high_variability = club_summary.sort_values("std_carry", ascending=False).head(3)
    st.dataframe(
        high_variability[["club", "std_carry"]].style.format({"std_carry": "{:.1f}"})
    )

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

    for club, club_df in df_filtered.groupby("club"):
        with st.expander(f"{club} details"):
            st.write(
                club_df[["carry_distance", "ball_speed", "launch_angle", "spin_rate"]].describe()
            )

# ---------------------------------------------------------------------------
with benchmark_tab:
    st.subheader("Club Benchmarking")

    required = [
        "club",
        "session_name",
        "carry_distance",
        "ball_speed",
        "launch_angle",
        "spin_rate",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("❌ Missing required columns: " + ", ".join(missing))
        st.stop()

    clubs = sorted(df["club"].dropna().unique())
    selected_club = st.selectbox("Select Club", clubs)
    session_options = ["All Sessions"] + sorted(df["session_name"].dropna().unique())
    selected_session_bm = st.selectbox(
        "Filter by Session", session_options, key="bm_session"
    )
    df_filtered = df[df["club"] == selected_club]
    if selected_session_bm != "All Sessions":
        df_filtered = df_filtered[df_filtered["session_name"] == selected_session_bm]

    has_offline = (
        "offline_distance" in df_filtered.columns
        and df_filtered["offline_distance"].notna().any()
    )

    st.markdown("### Shot Metrics")
    metrics = [
        {
            "Metric": "Carry Distance",
            "Average": df_filtered["carry_distance"].mean(),
            "Std Dev": df_filtered["carry_distance"].std(),
        },
        {
            "Metric": "Ball Speed",
            "Average": df_filtered["ball_speed"].mean(),
            "Std Dev": df_filtered["ball_speed"].std(),
        },
        {
            "Metric": "Launch Angle",
            "Average": df_filtered["launch_angle"].mean(),
            "Std Dev": df_filtered["launch_angle"].std(),
        },
        {
            "Metric": "Spin Rate",
            "Average": df_filtered["spin_rate"].mean(),
            "Std Dev": df_filtered["spin_rate"].std(),
        },
    ]
    if has_offline:
        metrics.append(
            {
                "Metric": "Offline Distance",
                "Average": df_filtered["offline_distance"].mean(),
                "Std Dev": df_filtered["offline_distance"].std(),
            }
        )
    if "total_distance" in df_filtered:
        metrics.insert(
            1,
            {
                "Metric": "Total Distance",
                "Average": df_filtered["total_distance"].mean(),
                "Std Dev": df_filtered["total_distance"].std(),
            },
        )

    metrics_df = pd.DataFrame(metrics)
    metrics_df["Average"] = metrics_df["Average"].round(1)
    metrics_df["Std Dev"] = metrics_df["Std Dev"].fillna("-").apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else x
    )
    st.dataframe(metrics_df, use_container_width=True)
    if not has_offline:
        st.info("Offline distance metrics not available.")

    fig_hist = px.histogram(
        df_filtered,
        x="carry_distance",
        nbins=20,
        title=f"Carry Distance Distribution – {selected_club}",
        labels={"carry_distance": "Carry Distance (yds)"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    if has_offline:
        fig_disp = px.scatter(
            df_filtered,
            x="offline_distance",
            y="carry_distance",
            title=f"Dispersion Plot – {selected_club}",
            labels={
                "offline_distance": "Offline Distance (yds)",
                "carry_distance": "Carry Distance (yds)",
            },
            hover_data=["session_name"],
        )
        fig_disp.update_traces(
            marker=dict(size=8, opacity=0.7, line=dict(width=1, color="DarkSlateGrey"))
        )
        st.plotly_chart(fig_disp, use_container_width=True)
    else:
        st.info("Offline distance data not available for dispersion plot.")

    st.markdown("## 🧠 Coach’s Feedback")
    carry_std = df_filtered["carry_distance"].std()
    offline_std = df_filtered["offline_distance"].std() if has_offline else None

    if pd.notna(carry_std) and carry_std > 15:
        st.warning(
            "⚠️ High inconsistency in carry distance – consider working on strike location and tempo control."
        )
    else:
        st.success("✅ Carry distance shows good consistency.")
    if offline_std is not None:
        if pd.notna(offline_std) and offline_std > 10:
            st.warning(
                "⚠️ Offline dispersion is wide – work on face angle or path to tighten dispersion."
            )
        else:
            st.success("✅ Directional control appears solid.")
