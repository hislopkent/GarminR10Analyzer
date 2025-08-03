import pandas as pd
import streamlit as st
from typing import List

@st.cache_data(show_spinner="Loading and caching session data...")
def load_sessions(uploaded_files: List, keep_all_columns: bool = False) -> pd.DataFrame:
    """
    Load and combine multiple Garmin R10 CSV files into one DataFrame.
    Renames 'Club Type' to 'Club', adds 'Session' column, trims unused columns if specified.
    """
    all_data = []
    columns_to_keep = ["Club", "Carry", "Launch Angle", "Smash Factor", "Backspin", "Session"]

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)

            # Rename 'Club Type' to 'Club'
            if "Club Type" in df.columns:
                df.rename(columns={"Club Type": "Club"}, inplace=True)

            df["Session"] = file.name.split(".")[0]

            if "Club" in df.columns:
                df["Club"] = df["Club"].fillna("Unknown").astype("category")

            # Drop unused columns unless requested
            if not keep_all_columns:
                df = df[[col for col in columns_to_keep if col in df.columns]]

            all_data.append(df)
        except Exception as e:
            st.warning(f"Could not load {file.name}: {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)
