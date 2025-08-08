import io
import pandas as pd

from utils.session_loader import load_sessions


def _make_file(content: str, name: str):
    buf = io.StringIO(content)
    buf.name = name
    return buf


def test_load_sessions_names_by_date():
    f1 = _make_file("Date,Club\n2025-08-01 10:00,Driver\n", "a.csv")
    f2 = _make_file("Date,Club\n2025-08-02 09:00,Driver\n", "b.csv")
    df = load_sessions([f1, f2])
    names = df["Session Name"].drop_duplicates().tolist()
    assert names == ["2025-08-01 Session 1", "2025-08-02 Session 1"]
    assert set(df["Source File"].unique()) == {"a.csv", "b.csv"}
    assert "Session ID" in df.columns
    assert len(df["Session ID"].unique()) == 2


def test_load_sessions_numbers_duplicate_dates():
    later = _make_file("Date,Club\n2025-08-01 15:00,Driver\n", "late.csv")
    earlier = _make_file("Date,Club\n2025-08-01 09:00,Driver\n", "early.csv")
    df = load_sessions([later, earlier])
    names = df["Session Name"].drop_duplicates().tolist()
    assert names == ["2025-08-01 Session 1", "2025-08-01 Session 2"]
    assert df["Session ID"].nunique() == 2


def test_load_sessions_club_fallback():
    """If the ``Club`` column is missing the loader should fall back to
    ``Club Name`` or ``Club Type``."""

    f = _make_file("Date,Club Name\n2025-08-01 10:00,Driver\n", "a.csv")
    df = load_sessions([f])
    assert "Club" in df.columns
    assert df.loc[0, "Club"] == "Driver"
