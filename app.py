
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Garmin R10 Multi-Session Analyzer with AI Summaries")

st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")
uploaded_files = st.file_uploader("Upload one or more Garmin R10 CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)
        df['Session'] = uploaded_file.name

        if 'Club Type' not in df.columns:
            st.warning(f"The following required columns are missing in {uploaded_file.name}: Club Type")
            continue

        df.rename(columns={'Club Type': 'Club'}, inplace=True)
        dfs.append(df)

    if not dfs:
        st.stop()

    df_all = pd.concat(dfs, ignore_index=True)

    # Data validation
    df_all = df_all.dropna(subset=['Club'])

    # Session filter
    try:
        df_all['Session'] = df_all['Session'].astype(str)
        sessions = sorted([str(s) for s in df_all["Session"].unique()])
    except Exception as e:
        sessions = []
        st.error(f"Session error: {e}")

    selected_session = st.selectbox("Filter by session", ["All Sessions"] + sessions)

    if selected_session != "All Sessions":
        df_all = df_all[df_all["Session"] == selected_session]

    # Club filter
    try:
        df_all['Club'] = df_all['Club'].astype(str)
        clubs = sorted([str(c) for c in df_all['Club'].unique()])
    except Exception as e:
        clubs = []
        st.error(f"Club error: {e}")

    selected_club = st.selectbox("Select a club", clubs)

    filtered = df_all[df_all['Club'] == selected_club]
    st.dataframe(filtered)

    # Download button
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Filtered CSV", csv, "filtered_data.csv", "text/csv")

    # Summary stats
    st.subheader("📈 Key Metrics Summary")
    numeric_cols = filtered.select_dtypes(include='number').columns
    if not numeric_cols.empty:
        summary = filtered[numeric_cols].describe().round(2)
        st.dataframe(summary)
    else:
        st.info("No numeric columns available for summary.")

    # Chart visualizer
    st.subheader("📊 Visuals")
    chart_metric = st.selectbox("Select metric to chart", numeric_cols)

    if chart_metric:
        fig, ax = plt.subplots()
        filtered[chart_metric].plot(kind='hist', bins=15, ax=ax, title=f"{chart_metric} Distribution")
        st.pyplot(fig)

    # AI Summary Placeholder
    st.subheader("🧠 AI Summary (coming soon)")
    st.write("AI-generated feedback based on your session data will appear here.")
