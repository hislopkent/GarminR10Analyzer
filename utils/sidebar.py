import streamlit as st


def render_sidebar() -> None:
    """Render navigation links in the sidebar for all pages.

    Uses :func:`st.sidebar.page_link` to provide consistent navigation
    between the main app and its sub-pages.
    """
    st.sidebar.title("Navigation")
    st.sidebar.page_link("Home.py", label="🏠 Home")
    st.sidebar.page_link("pages/0_Analysis.py", label="📈 Analysis")
    st.sidebar.page_link("pages/1_Sessions.py", label="📋 Sessions")
    st.sidebar.page_link("pages/2_Benchmark_Report.py", label="📌 Benchmark Report")
    st.sidebar.page_link("pages/3_AI_Feedback.py", label="🧠 AI Feedback")
