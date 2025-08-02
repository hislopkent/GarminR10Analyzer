
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Garmin R10 Analyzer with AI Summaries", layout="wide")

st.title("📊 Garmin R10 Analyzer with AI Summaries")
st.markdown("Upload your Garmin R10 CSV")

uploaded_file = st.file_uploader("Drag and drop file here", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [col.strip() for col in df.columns]

    # Detect club column
    club_column = None
    for col in ["Club", "Club Name", "Club Type"]:
        if col in df.columns:
            club_column = col
            break

    if club_column:
        df[club_column] = df[club_column].fillna("Unknown")
        available_clubs = df[club_column].dropna().unique()

        selected_club = st.selectbox("Select a club", available_clubs)

        filtered_data = df[df[club_column] == selected_club]

        st.subheader(f"Raw data for {selected_club}")
        st.dataframe(filtered_data)

        if len(filtered_data) >= 3:
            st.success("Summary is being generated...")
            # Placeholder for summary logic
        else:
            st.warning("Not enough data for summary.")
    else:
        st.warning("No recognizable club column found in your data.")
