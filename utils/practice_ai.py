"""Utilities for generating practice feedback summaries using OpenAI."""

import pandas as pd
import numpy as np
from .data_utils import coerce_numeric, remove_outliers
from .benchmarks import get_benchmarks
from .openai_utils import get_openai_client


def analyze_club_stats(
    df: pd.DataFrame,
    club: str,
    *,
    filter_outliers: bool = True,
    with_summary: bool = True,
) -> dict | None:
    """Analyse shots for a single club and return issues and optionally an AI summary.

    ``filter_outliers`` controls whether extreme values are removed prior to
    computing statistics. Outlier removal is enabled by default but can be
    disabled by passing ``False``. Set ``with_summary`` to ``False`` to skip the
    expensive OpenAI call and return only detected issues and stats.
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

    def _left_bias(x):
        return (x < 0).mean() * 100

    def _right_bias(x):
        return (x > 0).mean() * 100

    _left_bias.__name__ = "left_bias"
    _right_bias.__name__ = "right_bias"

    agg_map = {
        "Smash Factor": "mean",
        "Launch Angle": "mean",
        "Spin Rate": "mean",
        "Carry Distance": ["mean", "std"],
        "Offline": ["mean", _left_bias, _right_bias],
    }
    agg_map = {k: v for k, v in agg_map.items() if k in club_df.columns}
    stats = club_df.agg(agg_map) if agg_map else pd.DataFrame()
    avg_smash = stats.at["mean", "Smash Factor"] if "Smash Factor" in stats.columns else np.nan
    avg_launch = stats.at["mean", "Launch Angle"] if "Launch Angle" in stats.columns else np.nan
    avg_spin = stats.at["mean", "Spin Rate"] if "Spin Rate" in stats.columns else np.nan
    avg_carry = stats.at["mean", "Carry Distance"] if "Carry Distance" in stats.columns else np.nan
    std_carry = stats.at["std", "Carry Distance"] if "Carry Distance" in stats.columns else np.nan
    avg_offline = stats.at["mean", "Offline"] if "Offline" in stats.columns else np.nan
    left_bias = stats.at["left_bias", "Offline"] if ("Offline" in stats.columns and "left_bias" in stats.index) else 0
    right_bias = stats.at["right_bias", "Offline"] if ("Offline" in stats.columns and "right_bias" in stats.index) else 0

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

    summary = summarize_with_ai(club, feedback) if with_summary else ""
    return {
        "club": club,
        "summary": summary,
        "issues": feedback,
        "max_good_carry": max_good_carry,
        "avg_carry": avg_carry,
        "avg_offline": avg_offline,
    }

def summarize_with_ai(club: str, issues: list[str]) -> str:
    """Ask the OpenAI API to summarise ``issues`` for ``club``."""

    if not issues:
        return f"Your {club} data looks solid — no major red flags detected. Nice work!"

    client = get_openai_client()
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
    df: pd.DataFrame, *, filter_outliers: bool = True, with_summary: bool = True
) -> list[dict]:
    """Generate practice feedback for each club in ``df``.

    ``filter_outliers`` mirrors the argument in :func:`analyze_club_stats` and
    controls whether per-club analysis removes outliers.  ``with_summary`` can be
    set to ``False`` to avoid calling OpenAI when only the issues or statistics
    are needed.
    """
    # ``df`` may come from arbitrary CSVs.  Guard against the ``Club`` column
    # being missing to avoid ``KeyError``s when the caller supplies malformed
    # data.
    if "Club" not in df.columns:
        return []
    clubs = df["Club"].dropna().unique()
    results: list[dict] = []
    for club in clubs:
        stats = analyze_club_stats(
            df, club, filter_outliers=filter_outliers, with_summary=with_summary
        )
        if stats is not None:
            results.append(stats)
    return results
