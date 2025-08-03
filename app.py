import streamlit as st
import pandas as pd
import numpy as np
import os
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")

render_sidebar()
st.title("Garmin R10 Multi-Session Analyzer")
st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")
