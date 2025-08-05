"""Helpers for generating natural language feedback via OpenAI APIs."""

from typing import Dict

import pandas as pd
from .data_utils import coerce_numeric
from .openai_utils import get_openai_client


def generate_ai_summary(club_name, df):
    """Return a short coaching-style summary for ``club_name``.

    The function calculates a few aggregate statistics for the selected club
    and feeds them to an OpenAI Assistant.  If the required credentials are not
    configured the function returns a friendly warning instead of raising an
    exception.
    """

    shots = df[df["Club"] == club_name]
    if shots.empty:
        return "No data for this club."

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

    client = get_openai_client()
    if client is None:
        return "⚠️ AI credentials missing."
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI summary error: {e}"


def generate_ai_batch_summaries(df) -> Dict[str, str]:
    """Generate AI feedback for multiple clubs using a single prompt.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing all shot data with a ``Club`` column.

    Returns
    -------
    Dict[str, str]
        Mapping of club name to the AI generated feedback string. If credentials
        are missing or an error occurs, each club maps to an error message.
    """

    if "Club" not in df.columns:
        return {}

    clubs = df["Club"].unique().tolist()
    if not clubs:
        return {}

    summaries = {club: "" for club in clubs}

    client = get_openai_client()
    if client is None:
        return {club: "⚠️ AI credentials missing." for club in clubs}

    # Build a combined prompt with statistics for each club
    sections = []
    for club in clubs:
        shots = df[df["Club"] == club]
        if shots.empty:
            continue
        carry_col = "Carry Distance" if "Carry Distance" in shots.columns else "Carry"
        shots = shots.copy()
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
        section = (
            f"{club}\n"
            f"- Carry: {carry:.1f} yds\n"
            f"- Smash: {smash:.2f}\n"
            f"- Launch: {launch:.1f}°\n"
            f"- Backspin: {backspin:.0f} rpm\n"
            f"- Std Dev (Carry): {std_dev:.1f}\n"
            f"- Shots: {shot_count}"
        )
        sections.append(section)

    if not sections:
        return {club: "No data for this club." for club in clubs}

    prompt = (
        "You're a golf performance coach trained in Jon Sherman's Four Foundations. "
        "I use a Garmin R10. Provide a short, actionable summary for each club "
        "below. Format your reply as 'Club: summary' for each club.\n\n" + "\n\n".join(sections)
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = response.choices[0].message.content
        current = None
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.endswith(":") and stripped[:-1] in summaries:
                current = stripped[:-1]
                summaries[current] = ""
                continue
            if ":" in stripped and stripped.split(":", 1)[0] in summaries and summaries[
                stripped.split(":", 1)[0]
            ] == "":
                current, msg = stripped.split(":", 1)
                current = current.strip()
                summaries[current] = msg.strip()
            elif current:
                summaries[current] += (" " if summaries[current] else "") + stripped

        return {club: (msg.strip() if msg else "⚠️ AI summary error") for club, msg in summaries.items()}

    except Exception as e:
        return {club: f"⚠️ AI summary error: {e}" for club in clubs}
