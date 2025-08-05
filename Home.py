"""Home page for the Garmin R10 Analyzer Streamlit app.

This module handles file uploads, session-state management and persistence
between reloads. Uploaded CSV files are combined into a single dataframe and
cached on disk so the user can navigate between pages without losing data.
"""

import json
import os

import pandas as pd
import streamlit as st

from utils.logger import logger
from utils.session_loader import load_sessions
from utils.responsive import configure_page

configure_page()
st.title("📊 Garmin R10 Analyzer")

CACHE_PATH = os.path.join("sample_data", "session_cache.json")


def persist_state() -> None:
    """Persist uploaded file names and dataframe to disk.

    Streamlit's session state is volatile when the app reloads.  To make the
    experience smoother, the list of uploaded files and the combined dataframe
    are serialized to ``CACHE_PATH``.  The cache is lightweight and can be
    safely deleted if it becomes corrupted.
    """

    data = {
        "files": st.session_state.get("uploaded_files", []),
        "df": st.session_state.get("session_df", pd.DataFrame()),
    }
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "files": data["files"],
                    "df": data["df"].to_json(orient="split"),
                },
                f,
            )
        logger.info("State persisted with %d file(s)", len(data["files"]))
    except (OSError, TypeError, ValueError) as exc:  # pragma: no cover
        logger.warning("Failed to persist state: %s", exc)


def _refresh_session_views() -> None:
    """Recompute derived session state like ``df_all`` and ``club_data``."""

    df = st.session_state.get("session_df", pd.DataFrame())
    st.session_state["df_all"] = df
    if "Club" in df.columns:
        st.session_state["club_data"] = {club: grp for club, grp in df.groupby("Club")}
    else:
        st.session_state["club_data"] = {}


def load_state() -> None:
    """Load previously persisted session state from disk if it exists."""

    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - rare
            logger.warning("Failed to load cached state: %s", exc)
            return
        st.session_state["uploaded_files"] = data.get("files", [])
        df_json = data.get("df")
        st.session_state["session_df"] = (
            pd.read_json(df_json, orient="split") if df_json else pd.DataFrame()
        )
        _refresh_session_views()


def _rerun() -> None:
    """Trigger a Streamlit rerun with backward compatibility."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover - Streamlit < 1.24
        st.experimental_rerun()


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
            _refresh_session_views()
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


def remove_file(name: str) -> None:
    """Remove a file and its associated rows from session state and cache."""

    if name in st.session_state["uploaded_files"]:
        st.session_state["uploaded_files"].remove(name)
        if "session_df" in st.session_state and not st.session_state["session_df"].empty:
            session_df = st.session_state["session_df"]
            if "Source File" in session_df.columns:
                st.session_state["session_df"] = session_df[
                    session_df["Source File"] != name
                ]
            elif "Session Name" in session_df.columns:
                st.session_state["session_df"] = session_df[
                    session_df["Session Name"] != name
                ]
            else:
                logger.warning(
                    "Missing 'Source File' column while removing %s", name
                )
            _refresh_session_views()
        persist_state()
        _rerun()


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
        _rerun()

