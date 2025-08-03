import streamlit as st
import pandas as pd
import numpy as np

st.title("📒 Practice Log")

try:
    st.info("This page will display past practice sessions and allow logging new entries.")
except Exception as e:
    st.warning(f"Could not load practice log: {e}")
