
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import base64
import datetime

st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")

st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")

uploaded_files = st.file_uploader("Upload one or more Garmin R10 CSV files", type="csv", accept_multiple_files=True)

@st.cache_data
def load_and_process_data(uploaded_files):
    df_all = pd.DataFrame()
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Club' not in df.columns:
                if 'Club Type' in df.columns:
                    df['Club'] = df['Club Type']
                else:
                    st.warning(f"Missing 'Club' or 'Club Type' in {uploaded_file.name}")
                    continue

            # Generate Session name based on timestamp with session index
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
                df = df.sort_values('Date')
                df['SessionDate'] = df['Date'].dt.strftime('%Y-%m-%d')
                df['SessionIndex'] = df.groupby('SessionDate').cumcount() // 25 + 1
                df['Session'] = df['SessionDate'] + ' Session ' + df['SessionIndex'].astype(str)
            else:
                df['Session'] = uploaded_file.name.replace(".csv", "")

            df_all = pd.concat([df_all, df], ignore_index=True)
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
    return df_all

if uploaded_files:
    df_all = load_and_process_data(uploaded_files)

    sessions = sorted(df_all["Session"].dropna().astype(str).unique())
    selected_session = st.selectbox("Filter by session", ["All Sessions"] + sessions)

    clubs = sorted(df_all["Club"].dropna().astype(str).unique())
    selected_club = st.selectbox("Select a club", clubs)

    filtered = df_all.copy()
    if selected_session != "All Sessions":
        filtered = filtered[filtered["Session"] == selected_session]
    if selected_club:
        filtered = filtered[filtered["Club"] == selected_club]

    st.subheader("📄 Download Filtered CSV")
    csv = filtered.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="filtered_data.csv">Download Filtered CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

    if not filtered.empty:
        st.subheader("📈 Key Metrics Summary")
        numeric_cols = filtered.select_dtypes(include=['number']).columns
        st.dataframe(filtered[numeric_cols].describe().T)

        st.subheader("📊 Visuals")
        selected_metric = st.selectbox("Select metric to chart", numeric_cols)
        fig, ax = plt.subplots()
        filtered.boxplot(column=selected_metric, by="Club", ax=ax)
        plt.title(f"{selected_metric} by Club")
        plt.suptitle("")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        st.subheader("💡 AI Summary")
        summary = f"You selected {selected_club} from {selected_session}. Mean {selected_metric}: {filtered[selected_metric].mean():.2f}."
        st.write(summary)
    else:
        st.warning("No data to display for selected filters.")
