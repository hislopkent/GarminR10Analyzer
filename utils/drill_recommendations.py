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
}


def _match_benchmark(club: str) -> Dict[str, float]:
    """Return benchmark dict matching ``club`` by name (case-insensitive)."""

    club_lower = club.lower()
    for name, bench in get_benchmarks().items():
        if name.lower() in club_lower:
            return bench
    return {}


def recommend_drills(df: pd.DataFrame) -> Dict[str, List[Recommendation]]:
    """Generate drill recommendations for each club in ``df``.

    Parameters
    ----------
    df:
        DataFrame containing at least ``Club Type``, ``Carry Distance``,
        ``Smash Factor`` and ``Launch Angle`` columns.

    Returns
    -------
    dict
        Mapping of club name to a list of :class:`Recommendation` objects.
    """

    recommendations: Dict[str, List[Recommendation]] = {}

    for club, club_df in df.groupby("Club Type"):
        recs: List[Recommendation] = []
        bench = _match_benchmark(club)

        if bench.get("Smash Factor") is not None:
            if club_df["Smash Factor"].min() < bench["Smash Factor"]:
                recs.append(_DRILLS["low_smash"])

        carry_std = club_df["Carry Distance"].std(ddof=0)
        if pd.notna(carry_std) and carry_std > 8:
            recs.append(_DRILLS["inconsistent_carry"])

        if bench.get("Launch Angle") is not None:
            mean_launch = club_df["Launch Angle"].mean()
            low, high = bench["Launch Angle"]
            if mean_launch < low or mean_launch > high:
                recs.append(_DRILLS["poor_launch"])

        recommendations[club] = recs

    return recommendations
