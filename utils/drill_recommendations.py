"""Utility for recommending practice drills based on club stats.

This module analyses a dataframe of Garmin R10 shots and returns
issue/drill recommendations for each club.  The recommendations are
loosely inspired by Jon Sherman style practice routines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .benchmarks import get_benchmarks
from .data_utils import coerce_numeric


@dataclass
class Recommendation:
    """Represents a practice recommendation for a club."""

    issue: str
    drill: str


_DRILLS: Dict[str, Recommendation] = {
    "low_smash": Recommendation(
        issue="Low smash factor",
        drill="Use Jon Sherman's tee gate drill to improve center-face contact.",
    ),
    "inconsistent_carry": Recommendation(
        issue="Inconsistent carry distance",
        drill="Practice Jon Sherman's three-ball ladder drill for better distance control.",
    ),
    "poor_launch": Recommendation(
        issue="Poor launch angle",
        drill="Try Jon Sherman's low-point control drill to dial in launch.",
    ),
    "high_wedge_launch": Recommendation(
        issue="Launch angle too high with wedge",
        drill="Use flighted wedge drills to lower trajectory.",
    ),
    "high_wedge_spin": Recommendation(
        issue="Excessive wedge backspin",
        drill="Practice controlling spin with partial-swing wedge drills.",
    ),
}


def _match_benchmark(club: str) -> Dict[str, float]:
    """Return benchmark dict matching ``club`` by name (case-insensitive)."""

    club_lower = club.lower()
    aliases = {"pitching wedge": "pw", "sand wedge": "sw"}
    for alias, repl in aliases.items():
        if alias in club_lower:
            club_lower = club_lower.replace(alias, repl)
            break

    for name, bench in get_benchmarks().items():
        if name.lower() in club_lower:
            return bench
    return {}


def recommend_drills(df: pd.DataFrame) -> Dict[str, List[Recommendation]]:
    """Generate drill recommendations for each club in ``df``.

    Parameters
    ----------
    df:
        DataFrame containing club shot data.  A ``Club Type`` column is
        expected, but if only ``Club`` is present it will be used instead.

    Returns
    -------
    dict
        Mapping of club name to a list of :class:`Recommendation` objects.
    """

    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated()]
    if "Club Type" not in df.columns and "Club" in df.columns:
        df = df.rename(columns={"Club": "Club Type"})
    if "Club Type" not in df.columns:
        return {}

    recommendations: Dict[str, List[Recommendation]] = {}

    for club, club_df in df.groupby("Club Type"):
        recs: List[Recommendation] = []
        bench = _match_benchmark(club)
        club_lower = club.lower()
        wedge_keywords = ["wedge", "pw", "sw", "gw", "lw", "aw"]
        is_wedge = any(keyword in club_lower for keyword in wedge_keywords)

        # Work on a copy and coerce relevant columns to numeric to avoid
        # ``TypeError`` when the source data contains strings or duplicate
        # column names.
        club_df = club_df.copy()
        for col in ["Smash Factor", "Carry Distance", "Launch Angle", "Backspin"]:
            if col in club_df.columns:
                club_df[col] = coerce_numeric(club_df[col])

        if bench.get("Smash Factor") is not None and "Smash Factor" in club_df.columns:
            if club_df["Smash Factor"].min() < bench["Smash Factor"]:
                recs.append(_DRILLS["low_smash"])

        if "Carry Distance" in club_df.columns:
            carry_std = club_df["Carry Distance"].std(ddof=0)
            if pd.notna(carry_std) and carry_std > 8:
                recs.append(_DRILLS["inconsistent_carry"])

        if bench.get("Launch Angle") is not None and "Launch Angle" in club_df.columns:
            mean_launch = club_df["Launch Angle"].mean()
            low, high = bench["Launch Angle"]
            if mean_launch < low or mean_launch > high:
                recs.append(_DRILLS["poor_launch"])

        if is_wedge:
            if "Launch Angle" in club_df.columns:
                mean_launch = club_df["Launch Angle"].mean()
                if mean_launch > 40:
                    recs.append(_DRILLS["high_wedge_launch"])
            if (
                bench.get("Backspin") is not None
                and "Backspin" in club_df.columns
            ):
                mean_spin = club_df["Backspin"].mean()
                _, high_spin = bench["Backspin"]
                if mean_spin > high_spin:
                    recs.append(_DRILLS["high_wedge_spin"])

        recommendations[club] = recs

    return recommendations
