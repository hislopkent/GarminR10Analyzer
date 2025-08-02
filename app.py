
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Garmin R10 Analyzer with AI Summaries")

st.title("📊 Garmin R10 Analyzer with AI Summaries")
st.write("Upload your Garmin R10 CSV")

uploaded_file = st.file_uploader("Choose a file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [col.strip() for col in df.columns]

    # Infer the club column
    club_col = None
    for possible in ["Club", "Club Name", "Club Type"]:
        if possible in df.columns:
            club_col = possible
            break

    if club_col:
        st.selectbox("Select a club", df[club_col].dropna().unique())
        st.dataframe(df)

        st.subheader("📈 AI Summary (Basic)")
        numeric_cols = df.select_dtypes(include="number")
        if not numeric_cols.empty:
            summary = numeric_cols.describe().T
            st.write(summary)
        else:
            st.warning("No numeric columns available for summary.")
    else:
        st.warning("No club column found. Please upload a compatible Garmin R10 file.")
