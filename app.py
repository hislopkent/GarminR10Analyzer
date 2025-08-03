import streamlit as st
from utils.logger import logger
from utils.session_loader import load_sessions

st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")
st.title("📊 Garmin R10 Analyzer")

# Ensure the session key exists so we can safely reference it later
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

uploaded_files = st.file_uploader(
    "Upload one or more Garmin CSV files",
    type=["csv"],
    accept_multiple_files=True
)

if uploaded_files:
    # Store newly uploaded files in session state
    st.session_state["uploaded_files"] = uploaded_files
    logger.info(f"{len(uploaded_files)} files uploaded and stored in session state")

    # Load and persist session data for use across pages
    df = load_sessions(uploaded_files)
    if not df.empty:
        st.session_state["session_df"] = df
        st.session_state["df_all"] = df
        if "Club" in df.columns:
            st.session_state["club_data"] = {club: grp for club, grp in df.groupby("Club")}
        else:
            st.session_state["club_data"] = {}

    st.success(f"✅ {len(uploaded_files)} file(s) uploaded. Navigate to any page to begin.")
elif st.session_state["uploaded_files"]:
    # Inform the user that files are already stored
    st.info(
        f"📁 {len(st.session_state['uploaded_files'])} file(s) currently stored. "
        "You can navigate to any page or clear them below."
    )
else:
    st.info("📤 Upload files here to begin.")

# Provide a way to clear uploaded files from session state
if st.session_state["uploaded_files"]:
    if st.button("Clear uploaded files"):
        st.session_state.pop("uploaded_files", None)
        st.session_state.pop("session_df", None)
        st.session_state.pop("df_all", None)
        st.session_state.pop("club_data", None)
        st.experimental_rerun()
