import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.header("📋 Sessions Viewer")

# CSS for compact tables
st.markdown("""<style>.dataframe {font-size: small; overflow-x: auto;}</style>""", unsafe_allow_html=True)

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
    if st.button("Go to Home (Upload)"):
        st.switch_page("app.py")
else:
    st.subheader("Full Processed Data")
    st.dataframe(df_all, use_container_width=True)
    st.info("Explore all shots above. Navigate to Home for uploads or Dashboard for summaries.")
