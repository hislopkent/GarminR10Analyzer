import streamlit as st
from utils.logger import logger
logger.info("📄 Page loaded: 0 Dashboard")
import pandas as pd
import plotly.express as px
import numpy as np

st.title("📊 Club Performance Dashboard")

# Expect session_df to be provided via st.session_state from app.py
if "session_df" not in st.session_state or st.session_state["session_df"].empty:
    st.info("Please upload session files from the Home page to view this dashboard.")
    st.stop()

club_data = st.session_state["club_data"]
if "Club" not in df.columns:
    st.error("❌ The uploaded data does not contain a 'Club' column. Please check your CSV files.")
    st.stop()

# Sidebar club selection
club_list = sorted(club_data.keys().dropna().unique())
selected_club = st.sidebar.selectbox("Select a club to view", club_list)

club_data = df[club_data.keys() == selected_club]

# Show basic stats
st.subheader(f"Stats for {selected_club}")
st.write(club_data.describe(include='all'))

# Plot carry distance distribution
if "Carry" in club_data.columns:
    st.plotly_chart(px.histogram(club_data, x="Carry", nbins=20, title="Carry Distance Distribution"))

# Launch angle and smash factor scatter plot
if "Launch Angle" in club_data.columns and "Smash Factor" in club_data.columns:
    st.plotly_chart(
        px.scatter(club_data, x="Launch Angle", y="Smash Factor", 
                   title="Launch Angle vs Smash Factor", trendline="ols")
    )
