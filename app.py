
import streamlit as st
import pandas as pd

st.title("Garmin R10 Data Analyzer Preview")
st.write("Upload your CSV data to preview club performance metrics.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Raw Data", df.head())

    if 'Club' in df.columns:
        selected_club = st.selectbox("Select Club", df['Club'].unique())
        filtered_df = df[df['Club'] == selected_club]
        st.write(f"### Data for {selected_club}", filtered_df.describe())
    else:
        st.warning("No 'Club' column found in your data.")
