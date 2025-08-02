
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Garmin R10 Multi-Session Analyzer with AI Summaries", layout="wide")
st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")

uploaded_files = st.file_uploader("Upload one or more Garmin R10 CSV files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        if 'Club Type' in df.columns:
            df = df.rename(columns={'Club Type': 'Club'})
        else:
            st.error(f"'Club Type' column is missing in {file.name}. Cannot process this file.")
            continue
        df['Session'] = file.name
        dfs.append(df)

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)

        # Data type cleanup
        df_all['Club'] = df_all['Club'].astype(str)
        df_all['Session'] = df_all['Session'].astype(str)

        st.markdown("### Filter by session")
        session_options = sorted(df_all['Session'].dropna().unique(), key=str)
        selected_session = st.selectbox("Select a session", options=["All Sessions"] + session_options)

        if selected_session != "All Sessions":
            df_all = df_all[df_all['Session'] == selected_session]

        st.markdown("### Select a club")
        club_options = sorted(df_all['Club'].dropna().unique(), key=str)
        selected_club = st.selectbox("Select a club", club_options)

        filtered_df = df_all[df_all['Club'] == selected_club]

        st.markdown(f"### Raw data for {selected_club}")
        st.dataframe(filtered_df)

        if not filtered_df.empty:
            st.download_button("📥 Download Filtered CSV", data=filtered_df.to_csv(index=False), file_name=f"{selected_club}_filtered.csv", mime="text/csv")

            st.markdown("### 📈 Key Metrics Summary")
            st.write(filtered_df.describe(include='all'))

            st.markdown("### 📊 Visuals")
            numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if numeric_columns:
                chart_metric = st.selectbox("Select metric to chart", options=numeric_columns)
                st.line_chart(filtered_df[chart_metric])
            else:
                st.warning("No numeric data available for charting.")
        else:
            st.warning("Not enough data for summary.")
