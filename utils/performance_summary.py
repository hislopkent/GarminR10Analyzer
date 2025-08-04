"""Generate a natural-language performance summary for a set of golf shots.

The main entry point is :func:`summarize_performance` which accepts a
``pandas.DataFrame`` of shot data. The function looks for common columns
produced by Garmin R10 exports (``Club``/``Club Type``, ``Carry Distance`` or
``Carry``, ``Offline`` etc.) and produces a brief natural-language summary.
No network access is required – the summary is based purely on simple
heuristics and the existing drill recommendation utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from .drill_recommendations import Recommendation, recommend_drills
from .benchmarks import get_benchmarks
from .data_utils import coerce_numeric


@dataclass
class MissCounts:
    """Keep counts for different miss types."""

    short_right: int = 0
    short_left: int = 0
    long_right: int = 0
    long_left: int = 0
    left: int = 0
    right: int = 0

    def most_common(self) -> str | None:
        """Return description of the most common miss or ``None`` if none."""

        mapping = {
            "short right": self.short_right,
            "short left": self.short_left,
            "long right": self.long_right,
            "long left": self.long_left,
            "left": self.left,
            "right": self.right,
        }
        miss, count = max(mapping.items(), key=lambda kv: kv[1])
        return miss if count > 0 else None


def _determine_miss(row, carry_col: str) -> tuple[str | None, str | None]:
    """Return ``(distance, direction)`` miss labels for ``row``.

    ``carry_col`` is the column name containing carry distance.
    """

    distance_miss = None
    direction_miss = None

    club = str(row.get("Club") or row.get("Club Type") or "")
    benchmarks = get_benchmarks()

    carry_val = row.get(carry_col)
    try:
        carry_val = float(carry_val)
    except (TypeError, ValueError):
        carry_val = None

    if carry_val is not None:
        bench_carry = None
        for key, vals in benchmarks.items():
            if key.lower() in club.lower() and "Carry" in vals:
                bench_carry = vals["Carry"]
                break
        if bench_carry is not None:
            diff = carry_val - bench_carry
            if diff < -5:
                distance_miss = "short"
            elif diff > 5:
                distance_miss = "long"

    offline_val = row.get("Offline")
    try:
        offline_val = float(offline_val)
    except (TypeError, ValueError):
        offline_val = None
    if offline_val is not None:
        if offline_val > 5:
            direction_miss = "right"
        elif offline_val < -5:
            direction_miss = "left"

    return distance_miss, direction_miss


def summarize_performance(df: pd.DataFrame) -> str:
    """Return a natural-language performance summary for ``df``."""

    if df.empty:
        return "No shot data available."

    df = df.copy()
    if "Club" not in df.columns and "Club Type" in df.columns:
        df["Club"] = df["Club Type"]

    carry_col = None
    for option in ("Carry Distance", "Carry"):
        if option in df.columns:
            carry_col = option
            df[carry_col] = coerce_numeric(df[carry_col])
            break

    if "Offline" in df.columns:
        df["Offline"] = coerce_numeric(df["Offline"])

    misses = MissCounts()
    if carry_col or "Offline" in df.columns:
        for row in df.itertuples(index=False):
            distance, direction = _determine_miss(row._asdict(), carry_col or "Carry Distance")
            if distance == "short" and direction == "right":
                misses.short_right += 1
            elif distance == "short" and direction == "left":
                misses.short_left += 1
            elif distance == "long" and direction == "right":
                misses.long_right += 1
            elif distance == "long" and direction == "left":
                misses.long_left += 1
            elif direction == "left" and distance is None:
                misses.left += 1
            elif direction == "right" and distance is None:
                misses.right += 1
    miss_desc = misses.most_common()

    drill_df = df.copy()
    if "Club Type" not in drill_df.columns and "Club" in drill_df.columns:
        drill_df = drill_df.rename(columns={"Club": "Club Type"})
    drill_map: Dict[str, list[Recommendation]] = recommend_drills(drill_df)
    drill_suggestion = None
    if drill_map:
        club_name, recs = max(
            drill_map.items(), key=lambda kv: len(kv[1]) if kv[1] else 0
        )
        if recs:
            issue = recs[0].issue
            drill_suggestion = recs[0].drill
            attention_text = f"{club_name} needs attention ({issue.lower()})."
        else:
            attention_text = f"{club_name} looks solid overall."
    else:
        attention_text = "No club-specific issues detected."

    parts = []
    if miss_desc:
        parts.append(f"Most common miss: {miss_desc}.")
    else:
        parts.append("Miss pattern not detected.")
    parts.append(attention_text)
    if drill_suggestion:
        parts.append(f"Practice tip: {drill_suggestion}")
    else:
        parts.append("Practice tip: keep working on balanced, target-focused reps.")

    return " ".join(parts)

