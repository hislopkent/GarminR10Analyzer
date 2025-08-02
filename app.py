
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Club Summary", layout="wide")
st.title("🏌️ Club Summary")

@st.cache_data
def load_data():
    if 'all_data' in st.session_state:
        return st.session_state['all_data']
    return pd.DataFrame()

df_all = load_data()

if df_all.empty:
    st.warning("No data loaded yet. Please visit the 'Session Upload & Viewer' page first.")
else:
    clubs = sorted(df_all["Club"].dropna().astype(str).unique())
    selected_club = st.selectbox("Select a club", clubs)
    filtered = df_all[df_all["Club"] == selected_club]

    st.subheader(f"📊 Summary for {selected_club}")
    numeric_cols = filtered.select_dtypes(include='number').columns
    st.dataframe(filtered[numeric_cols].describe().T)

    st.subheader("📈 Visualize Metric")
    selected_metric = st.selectbox("Metric", numeric_cols)
    fig, ax = plt.subplots()
    filtered[selected_metric].plot(kind='hist', bins=20, ax=ax, title=f"{selected_metric} Distribution")
    st.pyplot(fig)
