import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.header("📋 Sessions Viewer")

# CSS for compact tables
st.markdown("""
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
        .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
        .sidebar a {color: #2ca02c; text-decoration: none;}
        .sidebar a:hover {background-color: #228B22; text-decoration: underline;}
    </style>
""", unsafe_allow_html=True)

# Consistent sidebar navigation with links
st.sidebar.title("Navigation")
st.sidebar.markdown("""
- [🏠 Home (Upload CSVs)](/)
- [📋 Sessions Viewer](/1_Sessions_Viewer)
- [📊 Dashboard](/0_dashboard)
""", unsafe_allow_html=True)

# Conditional guidance
if 'df_all' not in st.session_state or st.session_state['df_all'].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    st.subheader("Full Processed Data")
    
    # 1. Add Session Selector: Filter by session name
    sessions = st.multiselect("Select Sessions to View", df_all['Session'].unique(), default=df_all['Session'].unique())
    filtered = df_all[df_all['Session'].isin(sessions)] if sessions else df_all
    
    # 2. Add Column Filter/Search: Allow column selection
    columns = st.multiselect("Select Columns to Display", filtered.columns.tolist(), default=filtered.columns.tolist())
    filtered = filtered[columns] if columns else filtered
    
    # Display filtered data
    st.dataframe(filtered, use_container_width=True)
    st.info("Explore all shots above. Navigate to Home for uploads or Dashboard for summaries.")
    
    # 3. Export Filtered Data: Download session-specific or column-filtered data
    st.download_button(
        label="Export Filtered Data",
        data=filtered.to_csv(index=False),
        file_name="filtered_sessions.csv",
        mime="text/csv"
    )
    
    # 4. Add Summary Stats Per Session: Small table summarizing each session
    if not filtered.empty:
        st.subheader("Summary Stats Per Session")
        session_summary = filtered.groupby('Session').agg({
            'Carry': 'mean',
            'Total': 'mean',
            'Smash Factor': 'mean'
        }).round(1).reset_index()
        session_summary.columns = ['Session', 'Avg Carry', 'Avg Total', 'Avg Smash Factor']
        st.dataframe(session_summary, use_container_width=True)
