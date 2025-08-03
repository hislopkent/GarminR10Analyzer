import streamlit as st
from utils.logger import logger

st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")
st.title("📊 Garmin R10 Analyzer")

uploaded_files = st.file_uploader(
    "Upload one or more Garmin CSV files",
    type=["csv"],
    accept_multiple_files=True
)

if uploaded_files:
    st.session_state["uploaded_files"] = uploaded_files
    logger.info(f"{len(uploaded_files)} files uploaded and stored in session state")
    st.experimental_rerun()
else:
    st.session_state.pop("uploaded_files", None)
