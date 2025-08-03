import streamlit as st
import streamlit as st
import os
import pandas as pd
import numpy as np
import openai
import plotly.express as px
import plotly.graph_objects as go

from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

# Password protection
PASSWORD = os.environ.get("PASSWORD") or "demo123"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Protected App")
    password = st.text_input("Enter password:", type="password")
    if password == PASSWORD:
        st.session_state["authenticated"] = True
        st.experimental_rerun()
    elif password:
        st.error("❌ Incorrect password")
    st.stop()

# Logout button
if st.button("🔓 Logout"):
    st.session_state["authenticated"] = False
    st.experimental_rerun()


from utils.sidebar import render_sidebar

st.set_page_config(layout="centered")
st.header("📋 Sessions Viewer")

# CSS for compact tables
st.markdown(
    """
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
        .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
        .sidebar a {color: #2ca02c; text-decoration: none;}
        .sidebar a:hover {background-color: #228B22; text-decoration: underline;}
    </style>
""",
    unsafe_allow_html=True,
)

render_sidebar()

# Conditional guidance
if "df_all" not in st.session_state or st.session_state["df_all"].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get("df_all")

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    st.subheader("Full Processed Data")
    st.dataframe(df_all, use_container_width=True)
    st.info("Explore all shots above. Navigate to Home for uploads or Dashboard for summaries.")
