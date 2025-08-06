import json
import os
from threading import Lock

import pandas as pd
import streamlit as st

from .logger import logger

CACHE_PATH = os.path.join("sample_data", "session_cache.json")
_persist_lock = Lock()

def persist_state() -> None:
    """Persist uploaded sessions, dataframe and metadata to disk."""
    data = {
        "sessions": st.session_state.get("uploaded_sessions", []),
        "df": st.session_state.get("session_df", pd.DataFrame()),
        "shot_tags": st.session_state.get("shot_tags", {}),
        "practice_log": st.session_state.get("practice_log", []),
        "session_ids": st.session_state.get("session_ids", {}),
    }
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        tmp_path = f"{CACHE_PATH}.tmp"
        with _persist_lock, open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "sessions": data["sessions"],
                    "df": data["df"].to_json(orient="split"),
                    "shot_tags": data["shot_tags"],
                    "practice_log": data["practice_log"],
                    "session_ids": data["session_ids"],
                },
                f,
            )
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CACHE_PATH)
        logger.info("State persisted with %d session(s)", len(data["sessions"]))
    except (OSError, TypeError, ValueError) as exc:  # pragma: no cover
        logger.warning("Failed to persist state: %s", exc)
