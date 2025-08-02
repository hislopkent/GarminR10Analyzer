
import streamlit as st
import pandas as pd

st.title("Garmin R10 Data Analyzer Preview")
st.write("Upload your CSV data to preview club performance metrics.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Raw Data", df.head())
	
    # Instead of checking for 'Club', use 'Club Name' or fallback
	if 'Club' not in df.columns:
    	if 'Club Type' in df.columns:
        	df['Club'] = df['Club Name']
    	elif 'Club Name ' in df.columns:
        	df['Club'] = df['Club Type']
    else:
        st.warning("No identifiable club column found.")
    