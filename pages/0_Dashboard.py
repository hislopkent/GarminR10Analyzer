import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

st.title("🏠 Dashboard")

st.markdown("This is a placeholder dashboard. Please upload your data and view analysis across the sidebar options.")

try:
    st.info("This would display your aggregated stats, charts, and summaries once data is uploaded.")
except Exception as e:
    st.warning(f"Dashboard loading issue: {e}")
