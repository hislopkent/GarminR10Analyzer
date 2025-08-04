"""Utilities for generating practice feedback summaries using OpenAI."""

import pandas as pd
import numpy as np
from openai import OpenAI
import os
from .data_utils import coerce_numeric, remove_outliers
from .benchmarks import get_benchmarks


def _get_client() -> OpenAI | None:
    """Return an OpenAI client if an API key is configured."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def analyze_club_stats(
    df: pd.DataFrame, club: str, *, filter_outliers: bool = True
) -> dict | None:
    """Analyse shots for a single club and return issues and an AI summary.

    ``filter_outliers`` controls whether extreme values are removed prior to
    computing statistics. Outlier removal is enabled by default but can be
    disabled by passing ``False``.
    """

    feedback = []
    club_df = df[df["Club"] == club].copy()

    if club_df.empty:
        return {"club": club, "issues": ["No data"], "summary": "No data available."}

    numeric_cols = [
        "Carry Distance",
        "Launch Angle",
        "Spin Rate",
        "Smash Factor",
        "Offline",
    ]

    # Clean and cast existing columns only
    for col in numeric_cols:
        if col in club_df.columns:
            club_df[col] = coerce_numeric(club_df[col])

    # Remove outliers so a few wild shots don't skew statistics
    if filter_outliers:
        club_df = remove_outliers(club_df, numeric_cols)

    # Skip clubs without enough data to be meaningful
    if len(club_df) < 6:
        return None

    avg_smash = club_df["Smash Factor"].mean() if "Smash Factor" in club_df else np.nan
    avg_launch = club_df["Launch Angle"].mean() if "Launch Angle" in club_df else np.nan
    avg_spin = club_df["Spin Rate"].mean() if "Spin Rate" in club_df else np.nan
    avg_carry = club_df["Carry Distance"].mean() if "Carry Distance" in club_df else np.nan
    avg_offline = club_df["Offline"].mean() if "Offline" in club_df else np.nan
    std_carry = club_df["Carry Distance"].std() if "Carry Distance" in club_df else np.nan
    left_bias = (
        (club_df["Offline"] < 0).mean() * 100 if "Offline" in club_df else 0
    )
    right_bias = (
        (club_df["Offline"] > 0).mean() * 100 if "Offline" in club_df else 0
    )

    # Contact trends via smash factor
    if "Smash Factor" in club_df:
        smash = club_df["Smash Factor"].dropna()
        fat_rate = (smash < 1.2).mean() if not smash.empty else 0
        thin_rate = (smash > 1.5).mean() if not smash.empty else 0
        if fat_rate > 0.3:
            feedback.append(f"{fat_rate*100:.0f}% of shots were fat or chunked.")
        if thin_rate > 0.3:
            feedback.append(f"{thin_rate*100:.0f}% of shots were thin strikes.")
        if fat_rate <= 0.3 and thin_rate <= 0.3:
            if avg_smash < 1.2:
                feedback.append(
                    "Low smash factor suggests poor contact (fat or off-center hits)."
                )
            elif avg_smash > 1.5:
                feedback.append(
                    "High smash factor might mean thin or toe strikes."
                )

    if avg_launch < 10:
        feedback.append("Launch angle is too low — possibly de-lofted or poor strike.")
    elif avg_launch > 20 and "Wedge" not in club:
        feedback.append("Launch angle may be too high for this club.")

    if avg_spin < 4000 and "Wedge" not in club:
        feedback.append("Low spin rate can reduce stopping power and control.")
    elif avg_spin > 10000 and "Wedge" not in club:
        feedback.append("High spin could be from poor contact or wet range balls.")

    if left_bias > 60:
        feedback.append(
            f"You're missing left {left_bias:.0f}% of the time — face/path issue likely."
        )
    elif right_bias > 60:
        feedback.append(
            f"You're missing right {right_bias:.0f}% of the time — face/path issue likely."
        )

    if not np.isnan(avg_offline) and abs(avg_offline) > 10:
        direction = "left" if avg_offline < 0 else "right"
        feedback.append(
            f"Average shot is {abs(avg_offline):.0f} yds {direction} of target."
        )

    if std_carry > 15:
        feedback.append("High carry distance variability suggests inconsistent contact.")

    # Max carry of a good shot based on benchmarks
    benchmark_carry = None
    for key, vals in get_benchmarks().items():
        if key.lower() in club.lower() and "Carry" in vals:
            benchmark_carry = vals["Carry"]
            break

    max_good_carry = np.nan
    if "Carry Distance" in club_df:
        carries = club_df["Carry Distance"].dropna()
        if benchmark_carry is not None:
            good_shots = carries[carries >= 0.9 * benchmark_carry]
        else:
            good_shots = carries
        if not good_shots.empty:
            max_good_carry = good_shots.max()
            if benchmark_carry is not None:
                feedback.append(
                    f"Best good carry: {max_good_carry:.0f} yds (target {benchmark_carry} yds)."
                )

    if (
        benchmark_carry is not None
        and not np.isnan(avg_carry)
        and avg_carry < 0.8 * benchmark_carry
    ):
        feedback.append(
            f"Average carry {avg_carry:.0f} yds is below target {benchmark_carry} yds."
        )

    return {
        "club": club,
        "summary": summarize_with_ai(club, feedback),
        "issues": feedback,
        "max_good_carry": max_good_carry,
        "avg_carry": avg_carry,
        "avg_offline": avg_offline,
    }

def summarize_with_ai(club: str, issues: list[str]) -> str:
    """Ask the OpenAI API to summarise ``issues`` for ``club``."""

    if not issues:
        return f"Your {club} data looks solid — no major red flags detected. Nice work!"

    client = _get_client()
    if client is None:
        return "(AI summary disabled: no API key)"

    prompt = f"""
    A golfer hit a series of shots with a {club}. Based on these observations:
    - {chr(10).join(issues)}
    Give a concise 2–3 sentence summary in natural language, including 1 practical suggestion.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI summary failed: {e})"

def analyze_practice_session(
    df: pd.DataFrame, *, filter_outliers: bool = True
) -> list[dict]:
    """Generate practice feedback for each club in ``df``.

    ``filter_outliers`` mirrors the argument in :func:`analyze_club_stats` and
    controls whether per-club analysis removes outliers. It is enabled by
    default.
    """
    # ``df`` may come from arbitrary CSVs.  Guard against the ``Club`` column
    # being missing to avoid ``KeyError``s when the caller supplies malformed
    # data.
    if "Club" not in df.columns:
        return []
    clubs = df["Club"].dropna().unique()
    results: list[dict] = []
    for club in clubs:
        stats = analyze_club_stats(df, club, filter_outliers=filter_outliers)
        if stats is not None:
            results.append(stats)
    return results
