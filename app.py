import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")
st.title("Garmin R10 Multi-Session Analyzer")
st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")

# CSS for compact tables and navigation styling
st.markdown("""
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
        .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
    </style>
""", unsafe_allow_html=True)

# Consistent sidebar navigation across all pages
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", ["🏠 Home (Upload CSVs)", "📋 Sessions Viewer", "📊 Dashboard"])

if page == "📋 Sessions Viewer":
    st.switch_page("pages/1_Sessions_Viewer.py")
elif page == "📊 Dashboard":
    st.switch_page("pages/0_dashboard.py")

# Conditional guidance based on data
if 'df_all' not in st.session_state or st.session_state['df_all'].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

# Sample CSV format
st.markdown("""
### Expected CSV Format
Ensure your CSV includes:
- `Date`: Timestamp (e.g., "7/20/25 7:17:39 AM")
- `Club Type`: Club used (e.g., "5 Iron", "Driver")
- `Carry Distance`: Carry distance in yards
- Other columns: `Backspin`, `Sidespin`, `Total Distance`, `Smash Factor`, `Apex Height`
""")

def create_session_name(date_series):
    grouped = date_series.groupby(date_series.dt.date)
    renamed_sessions = []
    for day, group in grouped:
        sorted_times = group.sort_values()
        renamed_sessions.extend([f"{day} Session 1"] * len(sorted_times))
    return renamed_sessions

uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing CSVs..."):
        dfs = []
        total_rows = 0
        for idx, file in enumerate(uploaded_files):
            if file.size > 10 * 1024 * 1024:
                st.warning(f"File {file.name} exceeds 10MB. Consider splitting large files.")
                continue
            try:
                df = pd.read_csv(file)
                required_cols = ['Date', 'Club Type', 'Carry Distance']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"CSV {file.name} missing required columns: {required_cols}")
                    continue
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                if 'Club Type' in df.columns:
                    df.rename(columns={'Club Type': 'Club', 'Carry Distance': 'Carry', 'Total Distance': 'Total'}, inplace=True)
                    df['Carry'] = pd.to_numeric(df['Carry'], errors='coerce')
                    df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                dfs.append(df)
                total_rows += len(df)
                st.progress((idx + 1) / len(uploaded_files))
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
        
        if not dfs:
            st.error("No valid CSVs loaded. Please check your files and try again.")
        else:
            df_all = pd.concat(dfs, ignore_index=True)
            if 'Date' in df_all.columns:
                df_all = df_all.dropna(subset=['Date'])
                df_all['Session'] = create_session_name(df_all['Date'])
                unique_sessions = df_all['Session'].nunique()
                st.write(f"Debug: Number of unique sessions created: {unique_sessions}")
            st.session_state['df_all'] = df_all
            st.success(f"✅ Loaded {total_rows} shots from {len(dfs)} file(s).")
            st.dataframe(df_all.head(100), use_container_width=True)
            st.download_button(
                label="Download Processed Data",
                data=df_all.to_csv(index=False),
                file_name="processed_r10_data.csv",
                mime="text/csv"
            )
            if 'Carry' in df_all.columns:
                if df_all['Carry'].dtype == 'object':
                    st.warning("Carry column contains non-numeric data. Please check your CSV.")
                else:
                    avg_carry = df_all['Carry'].mean().round(1)
                    st.metric("Average Carry (All Clubs)", f"{avg_carry} yards")

if 'df_all' in st.session_state:
    if st.button("Clear Loaded Data"):
        del st.session_state['df_all']
        st.rerun()

else:
    st.info("Upload one or more Garmin R10 CSV files to begin.")
