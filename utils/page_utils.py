"""Shared Streamlit helpers for page-level operations."""

import streamlit as st

def require_data():
    """Return the session dataframe or stop with a warning.

    Many pages depend on data uploaded on the home page. This helper ensures
    that a dataframe is present in ``st.session_state`` and halts execution with
    a friendly message if not.
    """
    df = st.session_state.get("session_df")
    if df is None or df.empty:
        st.warning("📤 Please upload CSV files on the home page first.")
        st.stop()
    return df
