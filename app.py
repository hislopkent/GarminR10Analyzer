import streamlit as st
import osimport streamlit as stPASSWORD = os.environ.get("PASSWORD") or "demo123"if "authenticated" not in st.session_state:    st.session_state["authenticated"] = Falseif not st.session_state["authenticated"]:    st.title("🔒 Protected App")    password = st.text_input("Enter password:", type="password")    if password == PASSWORD:        st.session_state["authenticated"] = True        st.experimental_rerun()    elif password:        st.error("❌ Incorrect password")    st.stop()# Logout buttonif st.button("🔓 Logout"):    st.session_state["authenticated"] = False    st.experimental_rerun()import streamlit as st
    password = st.text_input("Enter password:", type="password")
        st.experimental_rerun()
    elif password:
        st.error("❌ Incorrect password")
    st.stop()

import pandas as pd
import numpy as np
from datetime import datetime
import os

MAX_FILE_SIZE_MB = 50

from utils.sidebar import render_sidebar

# Password validation
st.set_page_config(page_title="Garmin R10 Analyzer", layout="centered")
password = st.text_input("Enter Password", type="password")

if not correct_password:
elif password != correct_password:
    st.error("Incorrect password. Access denied.")
else:
    render_sidebar()
    st.title("Garmin R10 Multi-Session Analyzer")
    st.markdown(
        "Upload your Garmin R10 CSV files below to get started. View full data or analyze summaries via the sidebar."
    )

    # CSS for compact tables and navigation styling
    st.markdown(
        """
        <style>
            .dataframe {font-size: small; overflow-x: auto;}
            .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
            .sidebar a {color: #2ca02c; text-decoration: none;}
            .sidebar a:hover {background-color: #228B22; text-decoration: underline;}
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Conditional guidance based on data
    if "df_all" not in st.session_state or st.session_state["df_all"].empty:
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
    - Other columns: `Backspin`, `Sidespin`, `Total Distance`, `Smash Factor`, `Apex Height`, `Attack Angle`
    """)

    uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            MAX_SIZE = 10 * 1024 * 1024  # 10MB
            if file.size > MAX_SIZE:
                st.warning(f"{file.name} is too large to process. Try splitting the file.")
                continue

            content = file.read().decode("utf-8", errors="ignore")
            st.text_area(f"Preview of {file.name}", content[:1000], height=150)
            file.seek(0)  # reset for actual parsing

            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            st.error(f"❌ Failed to load {file.name}: {e}")


if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            MAX_SIZE = 10 * 1024 * 1024  # 10MB
            if file.size > MAX_SIZE:
                st.warning(f"{file.name} is too large to process. Try splitting the file.")
                continue

            content = file.read().decode("utf-8", errors="ignore")
            st.text_area(f"Preview of {file.name}", content[:1000], height=150)
            file.seek(0)  # reset for actual parsing

            all_data.append(df)
        except Exception as e:
            st.error(f"❌ Failed to load {file.name}: {e}")


    session_date = valid_dates.iloc[0]
                        else:
                            session_date = datetime.now().date()
                        session_counts[session_date] = session_counts.get(session_date, 0) + 1
                        df['Session'] = f"{session_date} Session {session_counts[session_date]}"
                    if 'Club Type' in df.columns:
                        df.rename(
                            columns={
                                'Club Type': 'Club',
                                'Carry Distance': 'Carry',
                                'Total Distance': 'Total',
                            },
                            inplace=True,
                        )
                        df['Carry'] = pd.to_numeric(df['Carry'], errors='coerce')
                        df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                    dfs.append(df)
                    total_rows += len(df)
                    st.progress((idx + 1) / len(uploaded_files))
                except Exception as e:
                    file.seek(0)
                    preview_lines = (
                        file.getvalue().decode('utf-8', errors='replace').splitlines()[:10]
                    )
                    preview_text = '\n'.join(preview_lines)
                    st.error(f"Failed to process {file.name}: {e}")
                    st.text("First 10 lines of the file for debugging:")
                    st.code(preview_text)

            if not dfs:
                st.error("No valid CSVs loaded. Please check your files and try again.")
            else:
                df_all = pd.concat(dfs, ignore_index=True)
                if 'Date' in df_all.columns:
                    df_all = df_all.dropna(subset=['Date'])
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