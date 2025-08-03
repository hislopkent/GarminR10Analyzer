import pandas as pd
import streamlit as st
from typing import List

def load_sessions(uploaded_files: List) -> pd.DataFrame:
    """
    Load and combine multiple Garmin R10 CSV files into one DataFrame.
    Adds a 'Session' column based on file name.
    """
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df["Session"] = file.name.split(".")[0]
            all_data.append(df)
        except Exception as e:
            st.warning(f"Could not load {file.name}: {e}")

    if not all_data:
        return pd.DataFrame()

    combined_df = pd.concat(all_data, ignore_index=True)

    # Standardize club names (optional)
    if "Club" in combined_df.columns:
        combined_df["Club"] = combined_df["Club"].fillna("Unknown").astype(str)

    return combined_df
