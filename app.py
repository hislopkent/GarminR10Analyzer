import os
import pickle

import pandas as pd
import streamlit as st

from utils.logger import logger
from utils.session_loader import load_sessions

st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")
st.title("📊 Garmin R10 Analyzer")

CACHE_PATH = os.path.join("sample_data", "session_cache.pkl")


def persist_state():
    """Persist uploaded file names and dataframe to disk."""
    data = {
        "files": st.session_state.get("uploaded_files", []),
        "df": st.session_state.get("session_df", pd.DataFrame()),
    }
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(data, f)
    logger.info("State persisted with %d file(s)", len(data["files"]))


def load_state():
    """Load any previously persisted state from disk."""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "rb") as f:
            data = pickle.load(f)
        st.session_state["uploaded_files"] = data.get("files", [])
        st.session_state["session_df"] = data.get("df", pd.DataFrame())
        st.session_state["df_all"] = st.session_state["session_df"]
        if "Club" in st.session_state["session_df"].columns:
            st.session_state["club_data"] = {
                club: grp
                for club, grp in st.session_state["session_df"].groupby("Club")
            }
        else:
            st.session_state["club_data"] = {}


# Initialize state on first run
if "uploaded_files" not in st.session_state:
    load_state()
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []


uploaded_files = st.file_uploader(
    "Upload one or more Garmin CSV files",
    type=["csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    existing = set(st.session_state.get("uploaded_files", []))
    new_files = [f for f in uploaded_files if f.name not in existing]
    dupes = [f.name for f in uploaded_files if f.name in existing]
    if dupes:
        st.warning("Skipping duplicate file(s): " + ", ".join(dupes))
    if new_files:
        df_new = load_sessions(new_files)
        if not df_new.empty:
            if (
                "session_df" in st.session_state
                and st.session_state["session_df"].shape[0] > 0
            ):
                st.session_state["session_df"] = pd.concat(
                    [st.session_state["session_df"], df_new], ignore_index=True
                )
            else:
                st.session_state["session_df"] = df_new
            st.session_state["df_all"] = st.session_state["session_df"]
            if "Club" in st.session_state["session_df"].columns:
                st.session_state["club_data"] = {
                    club: grp
                    for club, grp in st.session_state["session_df"].groupby("Club")
                }
            else:
                st.session_state["club_data"] = {}
        st.session_state["uploaded_files"].extend([f.name for f in new_files])
        persist_state()
        st.success(
            f"✅ {len(new_files)} new file(s) uploaded. Navigate to any page to begin."
        )
elif st.session_state.get("uploaded_files"):
    st.info(
        f"📁 {len(st.session_state['uploaded_files'])} file(s) currently stored. "
        "You can navigate to any page or clear/remove them below."
    )
else:
    st.info("📤 Upload files here to begin.")


def remove_file(name: str):
    """Remove a file and its data from session state."""
    if name in st.session_state["uploaded_files"]:
        st.session_state["uploaded_files"].remove(name)
        if "session_df" in st.session_state and not st.session_state["session_df"].empty:
            st.session_state["session_df"] = st.session_state["session_df"][
                st.session_state["session_df"]["Session Name"] != name
            ]
            st.session_state["df_all"] = st.session_state["session_df"]
            if "Club" in st.session_state["session_df"].columns:
                st.session_state["club_data"] = {
                    club: grp
                    for club, grp in st.session_state["session_df"].groupby("Club")
                }
            else:
                st.session_state["club_data"] = {}
        persist_state()
        st.experimental_rerun()


if st.session_state.get("uploaded_files"):
    st.subheader("Uploaded Sessions")
    for fname in st.session_state["uploaded_files"]:
        cols = st.columns([0.8, 0.2])
        cols[0].write(fname)
        if cols[1].button("Remove", key=f"rm_{fname}"):
            remove_file(fname)

    if st.button("Clear uploaded files"):
        st.session_state.pop("uploaded_files", None)
        st.session_state.pop("session_df", None)
        st.session_state.pop("df_all", None)
        st.session_state.pop("club_data", None)
        persist_state()
        st.experimental_rerun()

