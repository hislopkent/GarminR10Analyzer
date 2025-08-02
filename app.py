
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Garmin R10 Analyzer with AI Summaries", layout="wide")
st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")
st.write("Upload one or more Garmin R10 CSV files")

uploaded_files = st.file_uploader("Upload Garmin R10 CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        df = pd.read_csv(file)

        # Normalize column name
        if "Club Type" in df.columns and "Club" not in df.columns:
            df["Club"] = df["Club Type"]

        df["Session"] = file.name
        df_list.append(df)

    df_all = pd.concat(df_list, ignore_index=True)
    df_all.columns = [col.strip() for col in df_all.columns]

    try:
        sessions = sorted(df_all["Session"].dropna().unique(), key=str)
    except Exception as e:
        st.error(f"Session sorting error: {e}")
        sessions = ["All Sessions"]
    selected_session = st.selectbox("Select session", ["All Sessions"] + list(sessions))

    try:
        clubs = sorted(df_all["Club"].dropna().unique(), key=str)
    except Exception as e:
        st.error(f"Club sorting error: {e}")
        clubs = []
    selected_club = st.selectbox("Select a club", clubs if clubs else ["None"])

    if selected_session != "All Sessions":
        df_all = df_all[df_all["Session"] == selected_session]
    if selected_club != "None":
        df_all = df_all[df_all["Club"] == selected_club]

    if not df_all.empty:
        st.subheader(f"Filtered Data for {selected_club} in {selected_session}")
        st.dataframe(df_all)

        csv = df_all.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, file_name="filtered_data.csv")

        try:
            df_all["Club Speed"] = pd.to_numeric(df_all["Club Speed"], errors='coerce')
            df_all["Date"] = pd.to_datetime(df_all["Date"], errors='coerce')
            df_plot = df_all.dropna(subset=["Club Speed", "Date"]).sort_values("Date")

            plt.figure(figsize=(10, 4))
            plt.plot(df_plot["Date"], df_plot["Club Speed"], marker="o")
            plt.title(f"Club Speed Over Time - {selected_club}")
            plt.xlabel("Date")
            plt.ylabel("Club Speed (mph)")
            st.pyplot(plt)
        except Exception as e:
            st.warning(f"Plotting error: {e}")

        # Generate AI Summary
        st.markdown("### 🧠 AI Summary")
        try:
            summary_parts = []
            if "Ball Speed" in df_all.columns:
                ball_speed = df_all["Ball Speed"].dropna().astype(float)
                summary_parts.append(f"- Average Ball Speed: **{ball_speed.mean():.1f} mph**")

            if "Launch Angle" in df_all.columns:
                la = df_all["Launch Angle"].dropna().astype(float)
                summary_parts.append(f"- Launch Angle Range: **{la.min():.1f}° to {la.max():.1f}°**")

            if "Spin Rate" in df_all.columns:
                spin = df_all["Spin Rate"].dropna().astype(float)
                summary_parts.append(f"- Spin Rate Avg: **{spin.mean():.0f} rpm**")

            if "Carry Distance" in df_all.columns:
                carry = df_all["Carry Distance"].dropna().astype(float)
                summary_parts.append(f"- Average Carry Distance: **{carry.mean():.1f} yds**")

            if summary_parts:
                for line in summary_parts:
                    st.markdown(line)
            else:
                st.write("Not enough data available to generate summary.")

        except Exception as e:
            st.error(f"Error generating summary: {e}")
    else:
        st.warning("No data to display.")
