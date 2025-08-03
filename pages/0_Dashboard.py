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

df = st.session_state["session_df"].copy()

# Ensure a consistent club column name
if "Club" not in df.columns:
    if "Club Type" in df.columns:
        df["Club"] = df["Club Type"]
    else:
        st.error("❌ The uploaded data does not contain a 'Club' column. Please check your CSV files.")
        st.stop()

# Sidebar club selection
club_list = sorted(df["Club"].dropna().unique())
selected_club = st.sidebar.selectbox("Select a club to view", club_list)

club_data = df[df["Club"] == selected_club]

# Show basic stats
st.subheader(f"Stats for {selected_club}")
st.write(club_data.describe(include='all'))

# Plot carry distance distribution
if "Carry" in club_data.columns:
    st.plotly_chart(px.histogram(club_data, x="Carry", nbins=20, title="Carry Distance Distribution"))
elif "Carry Distance" in club_data.columns:
    st.plotly_chart(px.histogram(club_data, x="Carry Distance", nbins=20, title="Carry Distance Distribution"))

# Launch angle and smash factor scatter plot
if "Launch Angle" in club_data.columns and "Smash Factor" in club_data.columns:
    st.plotly_chart(
        px.scatter(club_data, x="Launch Angle", y="Smash Factor", title="Launch Angle vs Smash Factor", trendline="ols")
    )
