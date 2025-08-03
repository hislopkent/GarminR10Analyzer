"""Dashboard page showing key metrics, session filters and club statistics.

The dashboard expects session data to already be loaded into Streamlit's
session state by ``app.py``. Users can filter sessions, view aggregate
metrics, and drill into club-level statistics with Plotly visualisations.
"""

import streamlit as st
from utils.logger import logger
import pandas as pd
import plotly.express as px
import numpy as np

uploaded_files = st.session_state.get("uploaded_files", [])
if not uploaded_files:
    st.warning("📤 Please upload CSV files on the home page first.")
    st.stop()

logger.info("📄 Page loaded: 0 Dashboard")

st.title("📊 Club Performance Dashboard")

# Expect session_df to be provided via st.session_state from app.py
if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.info("Please upload session files from the Home page to view this dashboard.")
    st.stop()

df_all = st.session_state["session_df"].copy()

# Sidebar options to select which session(s) to analyse
session_names = df_all["Session Name"].dropna().unique().tolist()
st.sidebar.markdown("### Session Filters")
view_option = st.sidebar.selectbox(
    "Choose sessions to analyze",
    ["Latest Session", "Last 5 Sessions Combined", "Select Sessions"],
)

if "Date" in df_all.columns:
    df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")

if view_option == "Latest Session":
    if "Date" in df_all.columns and df_all["Date"].notna().any():
        latest_session = df_all.loc[df_all["Date"].idxmax(), "Session Name"]
    else:
        latest_session = session_names[-1]
    df_filtered = df_all[df_all["Session Name"] == latest_session]
elif view_option == "Last 5 Sessions Combined":
    if "Date" in df_all.columns and df_all["Date"].notna().any():
        session_order = (
            df_all.drop_duplicates("Session Name").sort_values("Date")
        )["Session Name"].tolist()
    else:
        session_order = session_names
    last_sessions = session_order[-5:]
    df_filtered = df_all[df_all["Session Name"].isin(last_sessions)]
else:  # Select Sessions
    chosen = st.sidebar.multiselect("Select session(s)", session_names)
    df_filtered = (
        df_all[df_all["Session Name"].isin(chosen)] if chosen else df_all.iloc[0:0]
    )

if df_filtered.empty:
    st.warning("No sessions selected.")
    st.stop()

df_filtered = df_filtered.copy()

# Ensure a consistent club column name
if "Club" not in df_filtered.columns:
    if "Club Type" in df_filtered.columns:
        df_filtered["Club"] = df_filtered["Club Type"]
    else:
        st.error(
            "❌ The uploaded data does not contain a 'Club' column. Please check your CSV files."
        )
        st.stop()

st.sidebar.markdown("### Club Filter")
club_options = sorted(df_filtered["Club"].dropna().unique())
selected_clubs = st.sidebar.multiselect("Select club(s)", club_options, default=club_options)

if not selected_clubs:
    st.warning("No clubs selected.")
    st.stop()

df_filtered = df_filtered[df_filtered["Club"].isin(selected_clubs)]
club_list = sorted(df_filtered["Club"].dropna().unique())

# Display key metrics for the filtered sessions
st.subheader("Key Metrics")

if "Carry Distance" in df_filtered.columns:
    avg_carry = df_filtered["Carry Distance"].mean()
elif "Carry" in df_filtered.columns:
    avg_carry = df_filtered["Carry"].mean()
else:
    avg_carry = np.nan

smash_factor = (
    df_filtered["Smash Factor"].mean()
    if "Smash Factor" in df_filtered.columns
    else np.nan
)

total_shots = len(df_filtered)

if "Face Impact Location" in df_filtered.columns:
    col = df_filtered["Face Impact Location"].astype(str)
    center_strike_pct = col.str.contains("center", case=False, na=False).mean() * 100
elif "Club Face Contact" in df_filtered.columns:
    col = df_filtered["Club Face Contact"].astype(str)
    center_strike_pct = col.str.contains("center", case=False, na=False).mean() * 100
else:
    center_strike_pct = np.nan

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Average Carry Distance",
    f"{avg_carry:.1f}" if not np.isnan(avg_carry) else "N/A",
)
col2.metric(
    "Smash Factor",
    f"{smash_factor:.2f}" if not np.isnan(smash_factor) else "N/A",
)
col3.metric("Total Shots", f"{total_shots}")
col4.metric(
    "Center Strike %",
    f"{center_strike_pct:.1f}%" if not np.isnan(center_strike_pct) else "N/A",
)

# Strike location distribution chart
if "strike_location" in df_filtered.columns:
    st.subheader("Strike Location Distribution")
    strike_counts = (
        df_filtered["strike_location"].astype(str).str.title().value_counts()
    )
    strike_counts = strike_counts.reindex(["Center", "Heel", "Toe"], fill_value=0)
    strike_df = strike_counts.reset_index()
    strike_df.columns = ["strike_location", "count"]
    strike_df["percentage"] = (
        strike_df["count"] / strike_df["count"].sum() * 100
        if strike_df["count"].sum() > 0
        else 0
    )
    fig_strike = px.bar(
        strike_df,
        x="percentage",
        y="strike_location",
        orientation="h",
        text="percentage",
        custom_data=["count"],
        labels={"percentage": "Percentage", "strike_location": "Strike Location"},
    )
    fig_strike.update_traces(
        texttemplate="%{x:.1f}%",
        hovertemplate="%{y}: %{x:.1f}% (%{customdata[0]} shots)<extra></extra>",
    )
    fig_strike.update_layout(xaxis=dict(ticksuffix="%"))
    st.plotly_chart(fig_strike, use_container_width=True)
else:
    st.info("No strike location data available.")

df = df_filtered.copy()
st.subheader("Shot Dispersion")
if "Offline" in df.columns:
    carry_col = "Carry Distance" if "Carry Distance" in df.columns else "Carry"
    if carry_col in df.columns:
        df["Offline"] = pd.to_numeric(df["Offline"], errors="coerce")
        df[carry_col] = pd.to_numeric(df[carry_col], errors="coerce")
        hover_cols = ["Date", "Club"] if "Date" in df.columns else ["Club"]
        fig_dispersion = px.scatter(
            df,
            x="Offline",
            y=carry_col,
            color="Club",
            hover_data=hover_cols,
            title="Lateral Dispersion vs Carry Distance",
        )
        st.plotly_chart(fig_dispersion, use_container_width=True)
    else:
        st.warning("No carry distance data available for dispersion plot.")
else:
    st.warning("No 'Offline' column available for dispersion plot.")

selected_club = st.sidebar.selectbox("Select a club to view", club_list)

club_data = df[df["Club"] == selected_club]

# Show basic stats
st.subheader(f"Stats for {selected_club}")
st.write(club_data.describe(include="all"))

# Plot carry distance distribution
if "Carry" in club_data.columns:
    st.plotly_chart(
        px.histogram(club_data, x="Carry", nbins=20, title="Carry Distance Distribution")
    )
elif "Carry Distance" in club_data.columns:
    st.plotly_chart(
        px.histogram(
            club_data, x="Carry Distance", nbins=20, title="Carry Distance Distribution"
        )
    )

# Launch angle and smash factor scatter plot
if "Launch Angle" in club_data.columns and "Smash Factor" in club_data.columns:
    st.plotly_chart(
        px.scatter(
            club_data,
            x="Launch Angle",
            y="Smash Factor",
            title="Launch Angle vs Smash Factor",
            trendline="ols",
        )
    )
