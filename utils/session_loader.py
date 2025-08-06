"""Utilities for loading and normalising Garmin session CSV files."""

from typing import List

import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from .data_utils import derive_offline_distance
from .logger import logger


def load_sessions(files: List[object]) -> pd.DataFrame:
    """Return a concatenated dataframe from uploaded CSV ``files``.

    Sessions are named using the earliest timestamp in each file.  If multiple
    files share the same date, a session number is appended based on the
    chronological order of their timestamps (e.g. ``2025-08-01`` and
    ``2025-08-01 #2``).  The original file name is preserved in the ``Source
    File`` column so files can still be removed individually later.

    Each file is read into a dataframe, normalised so that a ``Club`` column is
    always present and annotated with session metadata. Any files that fail to
    parse are skipped with a logged warning so errors are captured in
    ``app.log``.
    """

    def _load(file: object):
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            df = pd.read_csv(
                file, encoding="utf-8", encoding_errors="replace", on_bad_lines="error"
            )
            if "Club" not in df.columns and "Club Type" in df.columns:
                df["Club"] = df["Club Type"]
            df = derive_offline_distance(df)

            first_dt = pd.NaT
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                first_dt = df["Date"].min()

            return {
                "df": df,
                "first_dt": first_dt,
                "file_name": getattr(file, "name", "Unknown"),
            }
        except (OSError, pd.errors.ParserError, UnicodeError, AttributeError) as e:
            logger.warning(
                "Failed to load %s: %s", getattr(file, "name", "unknown"), e
            )
            return None

    max_workers = max(1, min(len(files), (os.cpu_count() or 1)))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        sessions = [s for s in pool.map(_load, files) if s]

    if not sessions:
        return pd.DataFrame()

    # Sort sessions by their earliest timestamp
    sessions.sort(key=lambda x: (pd.isna(x["first_dt"]), x["first_dt"]))

    # Assign session names, handling multiple sessions on the same date
    counts = {}
    dfs = []
    for session in sessions:
        df = session["df"]
        first_dt = session["first_dt"]
        file_name = session["file_name"]

        if pd.notna(first_dt):
            date_str = first_dt.date().isoformat()
            counts[date_str] = counts.get(date_str, 0) + 1
            count = counts[date_str]
            session_name = (
                f"{date_str} #{count}" if count > 1 else date_str
            )
        else:
            session_name = file_name

        df["Session Name"] = session_name
        df["Source File"] = file_name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)
