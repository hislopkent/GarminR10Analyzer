"""Combined dashboard and benchmarking analysis page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.logger import logger
from utils.data_utils import coerce_numeric, remove_outliers
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

if "offline_distance" not in df.columns and "side_distance" in df.columns:
    df["offline_distance"] = df["side_distance"]

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

session_names = df["session_name"].dropna().unique().tolist()
session_option = st.selectbox(
    "Choose sessions to analyze",
    ["All Sessions", "Latest Session", "Last 5 Sessions", "Select Sessions"],
)

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

if session_option == "All Sessions":
    df_filtered = df
elif session_option == "Latest Session":
    if "Date" in df.columns and df["Date"].notna().any():
        latest_session = df.loc[df["Date"].idxmax(), "session_name"]
    else:
        latest_session = session_names[-1] if session_names else None
    df_filtered = df[df["session_name"] == latest_session] if latest_session else df.iloc[0:0]
elif session_option == "Last 5 Sessions":
    if "Date" in df.columns and df["Date"].notna().any():
        session_order = (
            df.drop_duplicates("session_name").sort_values("Date")
        )["session_name"].tolist()
    else:
        session_order = session_names
    last_sessions = session_order[-5:]
    df_filtered = df[df["session_name"].isin(last_sessions)]
else:  # Select Sessions
    chosen = st.multiselect("Select session(s)", session_names)
    df_filtered = (
        df[df["session_name"].isin(chosen)] if chosen else df.iloc[0:0]
    )

filter_outliers = st.checkbox("Filter outliers", value=True)
if filter_outliers:
    numeric_cols = [
        "carry_distance",
        "total_distance",
        "ball_speed",
        "launch_angle",
        "spin_rate",
        "apex_height",
        "side_distance",
        "offline_distance",
    ]
    cols_present = [c for c in numeric_cols if c in df_filtered.columns]
    df_filtered = remove_outliers(df_filtered, cols_present)

overview_tab, benchmark_tab = st.tabs(["Overview", "Benchmarking"])

# ---------------------------------------------------------------------------
with overview_tab:
    st.subheader("Club Performance Overview")

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
    missing = [c for c in required if c not in df_filtered.columns]
    if missing:
        st.error("❌ Missing required columns: " + ", ".join(missing))
        st.stop()

    clubs = sorted(df_filtered["club"].dropna().unique())
    selected_club = st.selectbox("Select Club", clubs)
    session_options = ["All Sessions"] + sorted(
        df_filtered["session_name"].dropna().unique()
    )
    selected_session_bm = st.selectbox(
        "Filter by Session", session_options, key="bm_session"
    )
    club_df = df_filtered[df_filtered["club"] == selected_club]
    if selected_session_bm != "All Sessions":
        club_df = club_df[club_df["session_name"] == selected_session_bm]

    has_offline = (
        "offline_distance" in club_df.columns
        and club_df["offline_distance"].notna().any()
    )

    st.markdown("### Shot Metrics")
    metrics = [
        {
            "Metric": "Carry Distance",
            "Average": club_df["carry_distance"].mean(),
            "Std Dev": club_df["carry_distance"].std(),
        },
        {
            "Metric": "Ball Speed",
            "Average": club_df["ball_speed"].mean(),
            "Std Dev": club_df["ball_speed"].std(),
        },
        {
            "Metric": "Launch Angle",
            "Average": club_df["launch_angle"].mean(),
            "Std Dev": club_df["launch_angle"].std(),
        },
        {
            "Metric": "Spin Rate",
            "Average": club_df["spin_rate"].mean(),
            "Std Dev": club_df["spin_rate"].std(),
        },
    ]
    if has_offline:
        metrics.append(
            {
                "Metric": "Offline Distance",
                "Average": club_df["offline_distance"].mean(),
                "Std Dev": club_df["offline_distance"].std(),
            }
        )
    if "total_distance" in club_df:
        metrics.insert(
            1,
            {
                "Metric": "Total Distance",
                "Average": club_df["total_distance"].mean(),
                "Std Dev": club_df["total_distance"].std(),
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
        club_df,
        x="carry_distance",
        nbins=20,
        title=f"Carry Distance Distribution – {selected_club}",
        labels={"carry_distance": "Carry Distance (yds)"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    if has_offline:
        fig_disp = px.scatter(
            club_df,
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
    carry_std = club_df["carry_distance"].std()
    offline_std = club_df["offline_distance"].std() if has_offline else None

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
