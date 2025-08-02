
import streamlit as st
import pandas as pd
import openai
import os

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("🏌️ Garmin R10 Dashboard")

openai.api_key = os.getenv("OPENAI_API_KEY")

if 'all_data' not in st.session_state:
    st.warning("⚠️ No session data found. Please visit the 'Session Upload & Viewer' page first to upload your Garmin R10 files.")
    st.stop()

df_all = st.session_state['all_data']
required_columns = ['Club', 'Carry Distance', 'Back Spin', 'Off Center', 'Smash Factor', 'Apex Height', 'Total Distance']
missing_columns = [col for col in required_columns if col not in df_all.columns]

if missing_columns:
    st.error(f"Missing columns in uploaded data: {', '.join(missing_columns)}")
    st.stop()

def remove_outliers(df, columns):
    filtered_df = pd.DataFrame()
    for club in df['Club'].unique():
        club_df = df[df['Club'] == club]
        for col in columns:
            if club_df[col].dtype in ['float64', 'int64']:
                col_mean = club_df[col].mean()
                col_std = club_df[col].std()
                lower, upper = col_mean - 2.5 * col_std, col_mean + 2.5 * col_std
                club_df = club_df[(club_df[col] >= lower) & (club_df[col] <= upper)]
        filtered_df = pd.concat([filtered_df, club_df])
    return filtered_df

filter_outliers = st.toggle("🧹 Apply Smart Outlier Filter", value=True)

if filter_outliers:
    df_filtered = remove_outliers(df_all.copy(), required_columns[1:])
    st.success("Outlier filtering applied.")
else:
    df_filtered = df_all.copy()

summary = df_filtered.groupby('Club')[required_columns[1:]].mean().round(2)
st.dataframe(summary.style.format("{:.2f}"), use_container_width=True)

# Generate AI Summary
if st.button("🧠 Generate AI Summary"):
    try:
        clubs_summary = summary.reset_index().to_string(index=False)
        prompt = f"You are a golf coach reviewing Garmin R10 launch monitor data. Here is a summary of average metrics per club:\n{clubs_summary}\nWrite a brief and friendly analysis for the golfer, highlighting strengths, possible improvements, and anything unusual."

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a golf instructor who specializes in launch monitor data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        summary_text = response.choices[0].message.content
        st.subheader("🧠 AI Summary")
        st.write(summary_text)
    except Exception as e:
        st.error(f"Failed to generate summary: {e}")

st.info("📌 Tip: Upload more sessions on the 'Session Upload & Viewer' page to populate and compare club data here.")
