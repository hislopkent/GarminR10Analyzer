import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")
st.title("Garmin R10 Multi-Session Analyzer")
st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")

# CSS for compact tables
st.markdown("""<style>.dataframe {font-size: small; overflow-x: auto;}</style>""", unsafe_allow_html=True)

# Sidebar with descriptive labels
st.sidebar.success("Navigate:")
st.sidebar.markdown("- 🏠 Home (Upload CSVs)")
st.sidebar.markdown("- 📋 Sessions Viewer")
st.sidebar.markdown("- 📊 Dashboard")

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
        for idx, timestamp in enumerate(sorted_times):
            renamed_sessions.append(f"{day} Session {idx+1}")
    return renamed_sessions

uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing CSVs..."):
        dfs = []
        total_rows = 0
        for idx, file in enumerate(uploaded_files):
            # Check file size (e.g., warn if >10MB)
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
                    # Ensure numeric conversion after rename
                    df['Carry'] = pd.to_numeric(df['Carry'], errors='coerce')
                    df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                dfs.append(df)
                total_rows += len(df)
                # Update progress
                st.progress((idx + 1) / len(uploaded_files))
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
        
        if not dfs:
            st.error("No valid CSVs loaded. Please check your files and try again.")
        else:
            df_all = pd.concat(dfs, ignore_index=True)
            if 'Date' in df_all.columns:
                # Drop rows with invalid/NaT dates (e.g., units row)
                df_all = df_all.dropna(subset=['Date'])
                df_all['Session'] = create_session_name(df_all['Date'])
            st.session_state['df_all'] = df_all
            st.success(f"✅ Loaded {total_rows} shots from {len(dfs)} file(s).")
            st.dataframe(df_all.head(100), use_container_width=True)
            st.download_button(
                label="Download Processed Data",
                data=df_all.to_csv(index=False),
                file_name="processed_r10_data.csv",
                mime="text/csv"
            )
            # Quick metric with type checking
            if 'Carry' in df_all.columns:
                if df_all['Carry'].dtype == 'object':
                    st.warning("Carry column contains non-numeric data. Please check your CSV.")
                else:
                    avg_carry = df_all['Carry'].mean().round(1)
                    st.metric("Average Carry (All Clubs)", f"{avg_carry} yards")

# Clear data button
if 'df_all' in st.session_state:
    if st.button("Clear Loaded Data"):
        del st.session_state['df_all']
        st.rerun()

# Button to view full sessions
if 'df_all' in st.session_state:
    if st.button("View Full Sessions"):
        st.switch_page("pages/1_Sessions_Viewer.py")
else:
    st.info("Upload one or more Garmin R10 CSV files to begin.")