import pandas as pd
import streamlit as st
from typing import List

@st.cache_data(show_spinner="Loading and caching session data...")
def load_sessions(uploaded_files: List) -> pd.DataFrame:
    """
    Load and combine multiple Garmin R10 CSV files into one DataFrame.
    Renames 'Club Type' to 'Club', adds 'Session' column.
    """
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)

            # Rename 'Club Type' to 'Club' for consistency
            if "Club Type" in df.columns:
                df.rename(columns={"Club Type": "Club"}, inplace=True)

            df["Session"] = file.name.split(".")[0]

            if "Club" in df.columns:
                df["Club"] = df["Club"].fillna("Unknown").astype("category")

            all_data.append(df)
        except Exception as e:
            st.warning(f"Could not load {file.name}: {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)
