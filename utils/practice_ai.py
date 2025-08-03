"""Utilities for generating practice feedback summaries using OpenAI."""

import pandas as pd
import numpy as np
from openai import OpenAI
import os
from .data_utils import coerce_numeric

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_club_stats(df: pd.DataFrame, club: str) -> dict:
    """Analyse shots for a single club and return issues and an AI summary."""

    feedback = []
    club_df = df[df["Club"] == club].copy()

    if club_df.empty:
        return {"club": club, "issues": ["No data"], "summary": "No data available."}

    # Clean and cast existing columns only
    for col in ["Carry Distance", "Launch Angle", "Spin Rate", "Smash Factor", "Offline"]:
        if col in club_df.columns:
            club_df[col] = coerce_numeric(club_df[col])

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

    # Rules
    if avg_smash < 1.2:
        feedback.append("Low smash factor suggests poor contact (fat or off-center hits).")
    elif avg_smash > 1.5:
        feedback.append("High smash factor might mean thin or toe strikes.")

    if avg_launch < 10:
        feedback.append("Launch angle is too low — possibly de-lofted or poor strike.")
    elif avg_launch > 20 and "Wedge" not in club:
        feedback.append("Launch angle may be too high for this club.")

    if avg_spin < 4000 and "Wedge" not in club:
        feedback.append("Low spin rate can reduce stopping power and control.")
    elif avg_spin > 10000 and "Wedge" not in club:
        feedback.append("High spin could be from poor contact or wet range balls.")

    if left_bias > 60:
        feedback.append(f"You're missing left {left_bias:.0f}% of the time — face/path issue likely.")
    elif right_bias > 60:
        feedback.append(f"You're missing right {right_bias:.0f}% of the time — face/path issue likely.")

    if std_carry > 15:
        feedback.append("High carry distance variability suggests inconsistent contact.")

    return {
        "club": club,
        "summary": summarize_with_ai(club, feedback),
        "issues": feedback
    }

def summarize_with_ai(club: str, issues: list[str]) -> str:
    """Ask the OpenAI API to summarise ``issues`` for ``club``."""

    if not issues:
        return f"Your {club} data looks solid — no major red flags detected. Nice work!"

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

def analyze_practice_session(df: pd.DataFrame) -> list[dict]:
    """Generate practice feedback for each club in ``df``."""
    # ``df`` may come from arbitrary CSVs.  Guard against the ``Club`` column
    # being missing to avoid ``KeyError``s when the caller supplies malformed
    # data.
    if "Club" not in df.columns:
        return []
    clubs = df["Club"].dropna().unique()
    return [analyze_club_stats(df, club) for club in clubs]
