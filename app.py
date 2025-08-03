import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Password validation
st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")
password = st.text_input("Enter Password", type="password")
correct_password = os.environ.get("PASSWORD")

if not correct_password:
    st.error("Password not set in environment variables. Configure PASSWORD in Render dashboard.")
elif password != correct_password:
    st.error("Incorrect password. Access denied.")
else:
    st.title("Garmin R10 Multi-Session Analyzer")
    st.markdown("Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar.")

    # CSS for compact tables and navigation styling
    st.markdown("""
        <style>
            .dataframe {font-size: small; overflow-x: auto;}
            .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
            .sidebar a {color: #2ca02c; text-decoration: none; display: block; padding: 5px;}
            .sidebar a:hover {background-color: #228B22; color: white; text-decoration: none; border-radius: 3px;}
        </style>
    """, unsafe_allow_html=True)

    # Consistent sidebar navigation with single set of links
    st.sidebar.title("Navigation")
    st.sidebar.markdown("""
    - <a href="?" style="color: #2ca02c;">🏠 Home (Upload CSVs)</a>
    - <a href="?page=1_Sessions_Viewer" style="color: #2ca02c;">📋 Sessions Viewer</a>
    - <a href="?page=0_dashboard" style="color: #2ca02c;">📊 Dashboard</a>
    """, unsafe_allow_html=True)

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
        sessions = []
        prev_time = None
        session_counter = 1
        for current_time in date_series.sort_values():
            if prev_time and (current_time - prev_time).seconds > 1800:  # >30 min gap = new session
                session_counter += 1
            sessions.append(f"{current_time.date()} Session {session_counter}")
            prev_time = current_time
        return sessions

    uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        with st.spinner("Processing CSVs..."):
            dfs = []
            total_rows = 0
            for idx, file in enumerate(uploaded_files):
                if file.size > 50 * 1024 * 1024:
                    st.warning(f"File {file.name} exceeds 50MB. Skip or split the file.")
                    continue
                try:
                    df = pd.read_csv(file)
                    required_cols = ['Date', 'Club Type', 'Carry Distance', 'Backspin', 'Sidespin', 'Total Distance', 'Smash Factor', 'Apex Height']
                    missing = [col for col in required_cols if col not in df.columns]
                    if missing:
                        st.error(f"Missing columns in {file.name}: {missing}. File skipped.")
                        continue
                    # Standardize column names
                    df.columns = [col.strip().title() for col in df.columns]
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    if 'Club Type' in df.columns:
                        df.rename(columns={
                            'Club Type': 'Club',
                            'Carry Distance': 'Carry',
                            'Total Distance': 'Total',
                            'Backspin': 'Backspin',
                            'Sidespin': 'Sidespin',
                            'Smash Factor': 'Smash Factor',
                            'Apex Height': 'Apex Height'
                        }, inplace=True)
                        for col in ['Carry', 'Total', 'Backspin', 'Sidespin', 'Smash Factor', 'Apex Height']:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Initial outlier filtering
                    df = df[(df['Carry'] > 30) & (df['Carry'] < 400)]
                    Q1 = df['Carry'].quantile(0.25)
                    Q3 = df['Carry'].quantile(0.75)
                    IQR = Q3 - Q1
                    df = df[(df['Carry'] >= Q1 - 1.5 * IQR) & (df['Carry'] <= Q3 + 1.5 * IQR)]
                    dfs.append(df)
                    total_rows += len(df)
                    st.progress((idx + 1) / len(uploaded_files))
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}. File skipped. Check if it's a valid CSV.")
            
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
