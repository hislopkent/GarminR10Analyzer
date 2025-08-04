"""Utility functions for mobile-friendly responsive layouts."""

import streamlit as st


def configure_page() -> None:
    """Apply global page config and responsive CSS.

    Sets a wide layout for desktop use while injecting media-query CSS so the
    Streamlit app remains readable on small mobile screens.  The CSS reduces
    default padding and allows tab labels to wrap when the viewport is narrow.
    """

    st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")
    st.markdown(
        """
        <style>
        @media (max-width: 600px) {
            .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
