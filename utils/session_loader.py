"""Utilities for loading and normalising Garmin session CSV files."""

import pandas as pd
import io


def load_sessions(files):
    """Return a concatenated dataframe from uploaded CSV ``files``.

    Each file is read into a dataframe, annotated with the original file name
    and normalised so that a ``Club`` column is always present. Any files that
    fail to parse are skipped with a printed warning.
    """

    dfs = []
    for file in files:
        try:
            # ``UploadedFile`` objects from Streamlit expose ``getvalue``.
            # Fallback to ``read`` for generic file objects.  Accept both bytes
            # and text input, attempting UTF-8 decoding first and falling back to
            # latin-1 so unusual encodings don't immediately raise errors.
            if hasattr(file, "getvalue"):
                raw = file.getvalue()
            elif hasattr(file, "read"):
                raw = file.read()
            else:
                raise AttributeError("File object has no read() method")

            if isinstance(raw, bytes):
                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError:
                    content = raw.decode("latin-1")
            else:
                content = str(raw)

            df = pd.read_csv(io.StringIO(content))
            df["Session Name"] = getattr(file, "name", "Unknown")
            # Normalise club column name
            if "Club" not in df.columns and "Club Type" in df.columns:
                df["Club"] = df["Club Type"]
            dfs.append(df)
        except Exception as e:
            print(f"Failed to load {getattr(file, 'name', 'unknown')}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()
