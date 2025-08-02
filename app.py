
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Garmin R10 Analyzer", layout="wide")
st.title("📊 Garmin R10 Analyzer with AI Summaries")

uploaded_file = st.file_uploader("Upload your Garmin R10 CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Add fallback for club column
    if 'Club' not in df.columns:
        if 'Club Type' in df.columns:
            df['Club'] = df['Club Name']
        elif 'Club Name' in df.columns:
            df['Club'] = df['Club Type']
        else:
            st.warning("Could not detect club column.")
            st.stop()

    selected_club = st.selectbox("Select a club", sorted(df['Club'].unique()))
    club_df = df[df['Club'] == selected_club]

    st.subheader(f"Raw data for {selected_club}")
    st.dataframe(club_df)

    if len(club_df) > 5:
        st.subheader("📈 Smart Summary")
        st.write(f"Total shots: {len(club_df)}")

        carry_avg = club_df['Carry Distance'].mean()
        spin_avg = club_df['Spin Rate'].mean()
        launch_avg = club_df['Launch Angle'].mean()
        ball_speed_avg = club_df['Ball Speed'].mean()

        st.markdown(f"- **Avg Carry:** {carry_avg:.1f} yds")
        st.markdown(f"- **Avg Spin Rate:** {spin_avg:.0f} rpm")
        st.markdown(f"- **Avg Launch Angle:** {launch_avg:.1f}°")
        st.markdown(f"- **Avg Ball Speed:** {ball_speed_avg:.1f} mph")

        st.markdown("✅ Try filtering by club to compare dispersion, spin, and launch performance.")

    else:
        st.warning("Not enough data for summary.")
