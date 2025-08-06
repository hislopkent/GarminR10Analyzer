"""Home page for the Garmin R10 Analyzer Streamlit app.

This module handles file uploads, session-state management and persistence
between reloads. Uploaded CSV files are combined into a single dataframe and
cached on disk so the user can navigate between pages without losing data.
"""

import json
import os
import uuid

import pandas as pd
import streamlit as st

from utils.logger import logger
from utils.session_loader import load_sessions
from utils.responsive import configure_page
from utils.cache import persist_state, CACHE_PATH

configure_page()
st.title("📊 Garmin R10 Analyzer")

if "session_ids" not in st.session_state:
    st.session_state["session_ids"] = {}
if "shot_tags" not in st.session_state:
    st.session_state["shot_tags"] = {}
if "practice_log" not in st.session_state:
    st.session_state["practice_log"] = []


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
        st.session_state["uploaded_sessions"] = data.get("sessions", data.get("files", []))
        st.session_state["shot_tags"] = {
            int(k): v for k, v in data.get("shot_tags", {}).items()
        }
        st.session_state["practice_log"] = data.get("practice_log", [])
        st.session_state["session_ids"] = data.get("session_ids", {})

        df_json = data.get("df")
        if df_json:
            try:
                st.session_state["session_df"] = pd.read_json(
                    df_json, orient="split"
                )
            except ValueError as exc:  # pragma: no cover - rarely triggered
                logger.warning("Failed to parse cached dataframe: %s", exc)
                st.session_state["session_df"] = pd.DataFrame()
        else:
            st.session_state["session_df"] = pd.DataFrame()

        # If session IDs are missing but sessions are present, generate them
        if (
            st.session_state.get("session_df") is not None
            and not st.session_state["session_df"].empty
            and "Session ID" not in st.session_state["session_df"].columns
        ):
            sid_map = {}
            for sname in st.session_state["session_df"]["Session Name"].unique():
                sid = uuid.uuid4().hex
                sid_map[sname] = sid
                st.session_state["session_df"].loc[
                    st.session_state["session_df"]["Session Name"] == sname,
                    "Session ID",
                ] = sid
            st.session_state["session_ids"] = sid_map

        _refresh_session_views()


def _rerun() -> None:
    """Trigger a Streamlit rerun with backward compatibility."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover - Streamlit < 1.24
        st.experimental_rerun()


# Initialize state on first run
if "uploaded_sessions" not in st.session_state:
    load_state()
    if "uploaded_sessions" not in st.session_state:
        st.session_state["uploaded_sessions"] = []


uploaded_files = st.file_uploader(
    "Upload one or more Garmin CSV files",
    type=["csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    df_new = load_sessions(uploaded_files)
    existing = set(st.session_state.get("uploaded_sessions", []))
    new_names = df_new["Session Name"].drop_duplicates().tolist()
    dupes = [n for n in new_names if n in existing]
    if dupes:
        st.warning("Skipping duplicate session(s): " + ", ".join(dupes))
    df_new = df_new[~df_new["Session Name"].isin(dupes)]
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

        ids = (
            df_new[["Session ID", "Session Name"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for rec in ids:
            st.session_state["session_ids"][rec["Session Name"]] = rec["Session ID"]
        _refresh_session_views()
        st.session_state["uploaded_sessions"].extend(
            [name for name in new_names if name not in dupes]
        )
        persist_state()
        st.success(
            f"✅ {len(new_names) - len(dupes)} new session(s) uploaded. Navigate to any page to begin.",
        )
elif st.session_state.get("uploaded_sessions"):
    st.info(
        f"📁 {len(st.session_state['uploaded_sessions'])} session(s) currently stored. "
        "You can navigate to any page or clear/remove them below."
    )
else:
    st.info("📤 Upload files here to begin.")


def remove_session(name: str) -> None:
    """Remove a session and its associated rows from session state and cache."""

    if name not in st.session_state["uploaded_sessions"]:
        return
    st.session_state["uploaded_sessions"].remove(name)
    sid = st.session_state.get("session_ids", {}).pop(name, None)
    if (
        sid
        and "session_df" in st.session_state
        and not st.session_state["session_df"].empty
        and "Session ID" in st.session_state["session_df"].columns
    ):
        st.session_state["session_df"] = st.session_state["session_df"][
            st.session_state["session_df"]["Session ID"] != sid
        ]
        _refresh_session_views()
    persist_state()
    _rerun()


if st.session_state.get("uploaded_sessions"):
    st.subheader("Uploaded Sessions")
    for sname in st.session_state["uploaded_sessions"]:
        cols = st.columns([0.8, 0.2])
        cols[0].write(sname)
        if cols[1].button("Remove", key=f"rm_{sname}"):
            remove_session(sname)

    if st.button("Clear uploaded sessions"):
        st.session_state.pop("uploaded_sessions", None)
        st.session_state.pop("session_df", None)
        st.session_state.pop("df_all", None)
        st.session_state.pop("club_data", None)
        st.session_state.pop("session_ids", None)
        st.session_state.pop("shot_tags", None)
        persist_state()
        _rerun()

