"""Combined dashboard and benchmarking analysis page."""

from typing import Union

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.logger import logger
from utils.data_utils import (
    coerce_numeric,
    remove_outliers,
    classify_shots,
    IsolationForest,
)
from utils.constants import COLUMN_NORMALIZATION_MAP
from utils.page_utils import require_data
from utils.responsive import configure_page

logger.info("📄 Page loaded: Analysis")
configure_page()
st.title("📈 Analysis")

# Load and standardise data -------------------------------------------------
raw_df = require_data().copy()


@st.cache_data
def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={k: v for k, v in COLUMN_NORMALIZATION_MAP.items() if k in df.columns}
    )
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
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


df = _standardize(raw_df)
df_filtered = df.copy()
session_names = df["session_name"].dropna().unique().tolist()


@st.cache_data
def _apply_outlier_filter(
    df: pd.DataFrame,
    cols: tuple[str, ...],
    z: float,
    method: str,
    iqr: float,
    contamination: Union[float, str],
) -> pd.DataFrame:
    return remove_outliers(
        df,
        list(cols),
        z_thresh=z,
        iqr_mult=iqr,
        method=method,
        contamination=contamination,
    )


def _session_filter_ui(df: pd.DataFrame, session_names: list[str]) -> pd.DataFrame:
    session_option = st.selectbox(
        "Choose sessions to analyze",
        ["All Sessions", "Latest Session", "Last 5 Sessions", "Select Sessions"],
    )
    if session_option == "All Sessions":
        filtered = df
    elif session_option == "Latest Session":
        if "Date" in df.columns and df["Date"].notna().any():
            latest_session = df.loc[df["Date"].idxmax(), "session_name"]
        else:
            latest_session = session_names[-1] if session_names else None
        filtered = (
            df[df["session_name"] == latest_session]
            if latest_session
            else df.iloc[0:0]
        )
    elif session_option == "Last 5 Sessions":
        if "Date" in df.columns and df["Date"].notna().any():
            session_order = (
                df.drop_duplicates("session_name").sort_values("Date")
            )["session_name"].tolist()
        else:
            session_order = session_names
        last_sessions = session_order[-5:]
        filtered = df[df["session_name"].isin(last_sessions)]
    else:
        chosen = st.multiselect("Select session(s)", session_names)
        filtered = df[df["session_name"].isin(chosen)] if chosen else df.iloc[0:0]

    exclude = st.multiselect(
        "Exclude sessions from analysis",
        session_names,
        st.session_state.get("exclude_sessions", []),
    )
    st.session_state["exclude_sessions"] = exclude
    if exclude:
        filtered = filtered[~filtered["session_name"].isin(exclude)]
    return filtered


def _outlier_filter_ui(df: pd.DataFrame) -> pd.DataFrame:
    filter_outliers = st.checkbox(
        "Remove outliers",
        value=True,
        help="Drop shots with extreme values so a few wild swings don't skew averages",
    )
    if not filter_outliers:
        return df
    numeric_cols = (
        "carry_distance",
        "total_distance",
        "ball_speed",
        "launch_angle",
        "spin_rate",
        "apex_height",
        "side_distance",
        "offline_distance",
    )
    cols_present = [c for c in numeric_cols if c in df.columns]
    col_sel = st.multiselect("Outlier metrics", cols_present, default=cols_present)
    method_choice = st.radio(
        "Outlier detection",
        ["Statistical", "Adaptive"],
        help="Statistical uses z-scores/IQR; Adaptive uses Isolation Forest",
    )
    method = "isolation" if method_choice == "Adaptive" else "mad"
    if method == "isolation" and IsolationForest is None:
        st.warning(
            "scikit-learn required for adaptive method; using statistical instead",
        )
        method = "mad"
    iqr_mult = 1.5
    contamination = "auto"
    if method == "mad":
        z_thresh = st.slider("Z-score threshold", 1.0, 5.0, 3.0)
        iqr_mult = st.slider("IQR multiplier", 1.0, 3.0, 1.5)
    else:
        z_thresh = 3.0
        contamination = st.slider("Contamination", 0.01, 0.5, 0.1)
    if col_sel:
        before = df.copy()
        df = _apply_outlier_filter(
            df, tuple(col_sel), z_thresh, method, iqr_mult, contamination
        )
        removed = before.loc[~before.index.isin(df.index)]
        if not removed.empty:
            st.info(f"Removed {len(removed)} shots as outliers")
            with st.expander("Show removed outliers"):
                st.dataframe(removed)
    return df


def _quality_filter_ui(df: pd.DataFrame) -> pd.DataFrame:
    df = classify_shots(
        df, carry_col="carry_distance", offline_col="offline_distance"
    )
    if "shot_tags" in st.session_state:
        tag_map = st.session_state["shot_tags"]
        df.loc[df.index.intersection(tag_map.keys()), "Quality"] = df.index.map(
            tag_map
        )
    use_quality = st.checkbox(
        "Include only 'good' shots",
        value=False,
        help="Keep shots labelled as 'good' and ignore ones tagged 'miss' or 'outlier'",
    )
    if use_quality and "Quality" in df.columns:
        df = df[df["Quality"] == "good"]
    return df


with st.expander("Advanced Filters", expanded=False):
    df_filtered = _session_filter_ui(df, session_names)
    df_filtered = _outlier_filter_ui(df_filtered)
    df_filtered = _quality_filter_ui(df_filtered)
overview_tab, benchmark_tab = st.tabs(["Overview", "Benchmarking"])

# ---------------------------------------------------------------------------
with overview_tab:
    st.subheader("Club Performance Overview")

    club_summary = df_filtered.groupby("club").agg(
        total_shots=("carry_distance", "count"),
        avg_carry=("carry_distance", "mean"),
        median_carry=("carry_distance", "median"),
        p25_carry=("carry_distance", lambda x: x.quantile(0.25)),
        p75_carry=("carry_distance", lambda x: x.quantile(0.75)),
        std_carry=("carry_distance", "std"),
        avg_ball_speed=("ball_speed", "mean"),
        median_ball_speed=("ball_speed", "median"),
        avg_launch_angle=("launch_angle", "mean"),
        median_launch_angle=("launch_angle", "median"),
        avg_spin_rate=("spin_rate", "mean"),
        median_spin_rate=("spin_rate", "median"),
    ).reset_index()

    club_summary = club_summary[club_summary["total_shots"] >= 6]

    st.dataframe(
        club_summary.style.format(
            {
                "avg_carry": "{:.1f}",
                "median_carry": "{:.1f}",
                "p25_carry": "{:.1f}",
                "p75_carry": "{:.1f}",
                "std_carry": "{:.1f}",
                "avg_ball_speed": "{:.1f}",
                "median_ball_speed": "{:.1f}",
                "avg_launch_angle": "{:.1f}",
                "median_launch_angle": "{:.1f}",
                "avg_spin_rate": "{:.0f}",
                "median_spin_rate": "{:.0f}",
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

    if not club_summary.empty:
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
    carry_warn = st.slider("Carry variability warning (std yds)", 5.0, 30.0, 15.0)
    wedge_thresh = st.slider("Wedge low-carry threshold (yds)", 50.0, 150.0, 100.0)
    for _, row in club_summary.iterrows():
        if row["std_carry"] > carry_warn:
            st.warning(
                f"**{row['club']}** carry varies {row['std_carry']:.1f} yds. "
                f"Try a [tempo drill](https://www.golfdigest.com/story/golf-tempo-drills) to tighten dispersion."
            )
        if row["avg_carry"] < wedge_thresh and "wedge" in str(row["club"]).lower():
            st.info(
                f"**{row['club']}** carry seems low. Work on [ball-first contact](https://www.golf.com/instruction/solid-contact-drill)."
            )

    for club in club_summary["club"]:
        club_df = df_filtered[df_filtered["club"] == club]
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
            "Min": club_df["carry_distance"].min(),
            "Max": club_df["carry_distance"].max(),
            "P25": club_df["carry_distance"].quantile(0.25),
            "P75": club_df["carry_distance"].quantile(0.75),
        },
        {
            "Metric": "Ball Speed",
            "Average": club_df["ball_speed"].mean(),
            "Std Dev": club_df["ball_speed"].std(),
            "Min": club_df["ball_speed"].min(),
            "Max": club_df["ball_speed"].max(),
            "P25": club_df["ball_speed"].quantile(0.25),
            "P75": club_df["ball_speed"].quantile(0.75),
        },
        {
            "Metric": "Launch Angle",
            "Average": club_df["launch_angle"].mean(),
            "Std Dev": club_df["launch_angle"].std(),
            "Min": club_df["launch_angle"].min(),
            "Max": club_df["launch_angle"].max(),
            "P25": club_df["launch_angle"].quantile(0.25),
            "P75": club_df["launch_angle"].quantile(0.75),
        },
        {
            "Metric": "Spin Rate",
            "Average": club_df["spin_rate"].mean(),
            "Std Dev": club_df["spin_rate"].std(),
            "Min": club_df["spin_rate"].min(),
            "Max": club_df["spin_rate"].max(),
            "P25": club_df["spin_rate"].quantile(0.25),
            "P75": club_df["spin_rate"].quantile(0.75),
        },
    ]
    if has_offline:
        metrics.append(
            {
                "Metric": "Offline Distance",
                "Average": club_df["offline_distance"].mean(),
                "Std Dev": club_df["offline_distance"].std(),
                "Min": club_df["offline_distance"].min(),
                "Max": club_df["offline_distance"].max(),
                "P25": club_df["offline_distance"].quantile(0.25),
                "P75": club_df["offline_distance"].quantile(0.75),
            }
        )
    if "total_distance" in club_df:
        metrics.insert(
            1,
            {
                "Metric": "Total Distance",
                "Average": club_df["total_distance"].mean(),
                "Std Dev": club_df["total_distance"].std(),
                "Min": club_df["total_distance"].min(),
                "Max": club_df["total_distance"].max(),
                "P25": club_df["total_distance"].quantile(0.25),
                "P75": club_df["total_distance"].quantile(0.75),
            },
        )

    metrics_df = pd.DataFrame(metrics)
    metrics_df["Average"] = metrics_df["Average"].round(1)
    metrics_df["Std Dev"] = metrics_df["Std Dev"].fillna("-").apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else x
    )
    for col in ("Min", "Max", "P25", "P75"):
        if col in metrics_df.columns:
            metrics_df[col] = metrics_df[col].round(1)
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

    trend = (
        club_df.groupby("session_name")["carry_distance"].mean().reset_index()
    )
    if len(trend) > 1:
        fig_trend = px.line(
            trend,
            x="session_name",
            y="carry_distance",
            title=f"Carry Distance Trend – {selected_club}",
            labels={"carry_distance": "Avg Carry (yds)", "session_name": "Session"},
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("## 🧠 Coach’s Feedback")
    carry_std = club_df["carry_distance"].std()
    offline_std = club_df["offline_distance"].std() if has_offline else None
    carry_thresh = st.slider(
        "Carry consistency threshold (std yds)", 5.0, 30.0, 15.0, key="carry_fb"
    )
    offline_thresh = None
    if has_offline:
        offline_thresh = st.slider(
            "Offline dispersion threshold (std yds)", 5.0, 30.0, 10.0, key="offline_fb"
        )

    if pd.notna(carry_std) and carry_std > carry_thresh:
        st.warning(
            "⚠️ High inconsistency in carry distance – consider working on strike location and tempo control. "
            "Try the [three-ball ladder drill](https://practical-golf.com/three-ball-ladder-drill)."
        )
    else:
        st.success("✅ Carry distance shows good consistency.")
    if offline_std is not None and offline_thresh is not None:
        if pd.notna(offline_std) and offline_std > offline_thresh:
            st.warning(
                "⚠️ Offline dispersion is wide – work on face angle or path to tighten dispersion. "
                "[Gate drills](https://www.golfdigest.com/story/gate-drill) can help."
            )
        else:
            st.success("✅ Directional control appears solid.")
