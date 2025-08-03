# ai_feedback.py

import os
import openai


def generate_ai_summary(club_name, df):
    shots = df[df["Club"] == club_name]
    if shots.empty:
        return "No data for this club."

    carry = shots["Carry"].mean()
    smash = shots["Smash Factor"].mean()
    launch = shots["Launch Angle"].mean()
    backspin = shots["Backspin"].mean()
    std_dev = shots["Carry"].std()
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

    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    client = openai.OpenAI(api_key=api_key) if api_key else None

    if not client or not assistant_id:
        return "⚠️ AI credentials missing."
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )
        import time
        while run.status not in ["completed", "failed", "cancelled", "expired"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return messages.data[0].content[0].text.value
        return f"⚠️ AI summary error: {run.status}"
    except Exception as e:
        return f"⚠️ AI summary error: {str(e)}"
