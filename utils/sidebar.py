import streamlit as st


def render_sidebar() -> None:
    """Render navigation links in the sidebar for all pages."""
    st.sidebar.title("Navigation")
    st.sidebar.page_link("app.py", label="🏠 Home")
    st.sidebar.page_link("pages/0_Dashboard.py", label="📊 Club Dashboard")
    st.sidebar.page_link("pages/1_Sessions_Viewer.py", label="📋 Sessions Viewer")
    st.sidebar.page_link("pages/2_Benchmark_Report.py", label="📌 Benchmark Report")
