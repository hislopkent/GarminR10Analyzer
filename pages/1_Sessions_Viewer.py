import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.header("📋 Sessions Viewer")

# CSS for compact tables
st.markdown("""
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
    </style>
""", unsafe_allow_html=True)

# Consistent sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", ["🏠 Home (Upload CSVs)", "📋 Sessions Viewer", "📊 Dashboard"])

if page == "🏠 Home (Upload CSVs)":
    st.switch_page("app.py")
elif page == "📊 Dashboard":
    st.switch_page("pages/0_dashboard.py")

# Conditional guidance
if 'df_all' not in st.session_state or st.session_state['df_all'].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    st.subheader("Full Processed Data")
    st.dataframe(df_all, use_container_width=True)
    st.info("Explore all shots above. Navigate to Home for uploads or Dashboard for summaries.")
