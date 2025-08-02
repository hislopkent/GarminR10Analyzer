
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Session Upload & Viewer", layout="wide")
st.title("📂 Session Upload & Viewer")

uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

@st.cache_data
def process_files(files):
    all_data = pd.DataFrame()
    for file in files:
        df = pd.read_csv(file)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')
            df['SessionDate'] = df['Date'].dt.strftime('%Y-%m-%d')
            df['SessionIndex'] = df.groupby('SessionDate').cumcount() // 25 + 1
            df['Session'] = df['SessionDate'] + ' Session ' + df['SessionIndex'].astype(str)
        else:
            df['Session'] = file.name.replace(".csv", "")
        if 'Club' not in df.columns and 'Club Type' in df.columns:
            df['Club'] = df['Club Type']
        all_data = pd.concat([all_data, df], ignore_index=True)
    return all_data

if uploaded_files:
    df_all = process_files(uploaded_files)
    st.session_state['all_data'] = df_all

    st.subheader("🗂 Available Sessions")
    sessions = sorted(df_all['Session'].unique())
    selected_session = st.selectbox("Select session", sessions)
    session_df = df_all[df_all['Session'] == selected_session]
    st.dataframe(session_df)
