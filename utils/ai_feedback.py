"""Helpers for generating natural language feedback via OpenAI APIs."""

from typing import Dict, Any

import pandas as pd
from .data_utils import coerce_numeric
from .openai_utils import get_openai_client


def generate_ai_summary(club_name, df):
    """Return a short coaching-style summary and stats for ``club_name``.

    The function calculates a few aggregate statistics for the selected club
    and feeds them to an OpenAI Assistant. If credentials are missing the
    returned summary contains a friendly warning instead of raising an
    exception. Both the text summary and the underlying stats are returned so
    callers can display the numbers that informed the model's response.
    """

    shots = df[df["Club"] == club_name]
    if shots.empty:
        return "No data for this club.", {}

    carry_col = "Carry Distance" if "Carry Distance" in shots.columns else "Carry"
    shots = shots.copy()
    # Coerce numeric columns to floats; missing columns result in NaN values so
    # that formatting below does not raise ``TypeError``.
    if carry_col in shots.columns:
        shots[carry_col] = coerce_numeric(shots[carry_col])
    for col in ["Smash Factor", "Launch Angle", "Backspin"]:
        if col in shots.columns:
            shots[col] = coerce_numeric(shots[col])

    carry = shots[carry_col].mean() if carry_col in shots.columns else float("nan")
    smash = shots["Smash Factor"].mean() if "Smash Factor" in shots.columns else float("nan")
    launch = shots["Launch Angle"].mean() if "Launch Angle" in shots.columns else float("nan")
    backspin = shots["Backspin"].mean() if "Backspin" in shots.columns else float("nan")
    std_dev = shots[carry_col].std() if carry_col in shots.columns else float("nan")
    shot_count = len(shots)

    prompt = f"""
You're a golf performance coach trained in Jon Sherman's Four Foundations. I use a Garmin R10. Give me a short, actionable summary for my {club_name} based on these stats:

- Carry: {carry:.1f} yds
- Smash: {smash:.2f}
- Launch: {launch:.1f}°
- Backspin: {backspin:.0f} rpm
- Std Dev (Carry): {std_dev:.1f}
- Shots: {shot_count}

Explain what this means for my consistency and what to do in practice. Be specific and encouraging. Mention if anything is a standout or weak point.
"""

    stats = {
        "Carry": round(carry, 1) if carry == carry else carry,
        "Smash": round(smash, 2) if smash == smash else smash,
        "Launch": round(launch, 1) if launch == launch else launch,
        "Backspin": round(backspin) if backspin == backspin else backspin,
        "Std Dev": round(std_dev, 1) if std_dev == std_dev else std_dev,
        "Shots": shot_count,
    }

    client = get_openai_client()
    if client is None:
        return "⚠️ AI credentials missing.", stats
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        summary = f"⚠️ AI summary error: {e}"
    return summary, stats


def generate_ai_batch_summaries(df) -> Dict[str, Dict[str, Any]]:
    """Generate AI feedback for multiple clubs.

    Returns a mapping of club name to a dictionary containing the ``summary``
    text and the ``stats`` used to produce it. Each club is processed
    sequentially but callers only need to make a single function call.
    """

    if "Club" not in df.columns:
        return {}

    clubs = df["Club"].dropna().unique().tolist()
    summaries: Dict[str, Dict[str, Any]] = {}
    for club in clubs:
        summary, stats = generate_ai_summary(club, df)
        summaries[club] = {"summary": summary, "stats": stats}
    return summaries
