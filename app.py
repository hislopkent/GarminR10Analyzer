
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Garmin R10 Multi-Session Analyzer with AI Summaries")

st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")
st.markdown("Upload one or more Garmin R10 CSV files")

uploaded_files = st.file_uploader("Upload your Garmin R10 CSV", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)

        # Rename 'Club Type' to 'Club' for internal use
        if 'Club Type' in df.columns:
            df.rename(columns={'Club Type': 'Club'}, inplace=True)

        # Add a 'Session' column based on filename
        df["Session"] = uploaded_file.name
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    # Handle missing Club column
    if 'Club' not in df_all.columns:
        st.warning("The following required column is missing: Club")
    else:
        st.subheader("Filter by session")
        try:
            sessions = df_all["Session"].dropna().astype(str).unique()
            selected_session = st.selectbox("Select session", ["All Sessions"] + sorted(sessions))
        except Exception as e:
            st.error(f"Session filter error: {e}")
            selected_session = "All Sessions"

        st.subheader("Select a club")
        try:
            clubs = df_all["Club"].dropna().astype(str).unique()
            selected_club = st.selectbox("Select a club", sorted(clubs))
        except Exception as e:
            st.error(f"Club filter error: {e}")
            selected_club = None

        # Apply filters
        try:
            filtered = df_all[df_all["Club"] == selected_club]
            if selected_session != "All Sessions":
                filtered = filtered[filtered["Session"] == selected_session]
        except Exception as e:
            st.error(f"Filter application error: {e}")
            filtered = pd.DataFrame()

        if not filtered.empty:
            st.subheader("Filtered Data")
            st.dataframe(filtered)

            st.download_button("Download Filtered CSV", data=filtered.to_csv(index=False), file_name="filtered_data.csv")

            st.subheader("Club Speed Over Time")
            if "Club Speed" in filtered.columns:
                fig, ax = plt.subplots()
                filtered["Club Speed"] = pd.to_numeric(filtered["Club Speed"], errors="coerce")
                ax.plot(filtered["Club Speed"].reset_index(drop=True))
                ax.set_ylabel("Club Speed (mph)")
                ax.set_xlabel("Shot Number")
                ax.grid(True)
                st.pyplot(fig)
        else:
            st.warning("No data to display for selected filters.")
