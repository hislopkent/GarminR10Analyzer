
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Garmin R10 Multi-Session Analyzer", layout="wide")
st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")

uploaded_files = st.file_uploader("Upload one or more Garmin R10 CSV files", type="csv", accept_multiple_files=True)

required_columns = ['Club Type', 'Club Speed', 'Ball Speed', 'Smash Factor', 'Launch Angle', 'Backspin']

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
        if 'Club Type' in df.columns:
            df.rename(columns={'Club Type': 'Club'}, inplace=True)
            df["Session"] = file.name
            all_data.append(df)
        except Exception as e:
            st.error(f"Failed to read {file.name}: {e}")

    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)

        missing_cols = [col for col in required_columns if col not in df_all.columns]
        if missing_cols:
            st.warning(f"The following required columns are missing: {', '.join(missing_cols)}")
        else:
            for col in required_columns[1:]:  # skip 'Club'
                df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

            df_all['Club Type'] = df_all['Club Type'].astype(str)

            sessions = sorted(df_all["Session"].astype(str).unique())
            selected_session = st.selectbox("Filter by session", ["All Sessions"] + list(sessions))

            if selected_session != "All Sessions":
                df_all = df_all[df_all["Session"] == selected_session]

            clubs = sorted(df_all['Club Type'].dropna().unique())
            selected_club = st.selectbox("Select a club", clubs)

            filtered = df_all[df_all['Club'] == selected_club]

            st.subheader(f"Raw data for {selected_club} ({selected_session})")
            st.dataframe(filtered)

            # Download button
            st.download_button("📥 Download Filtered Data as CSV", data=filtered.to_csv(index=False), file_name=f"{selected_club}_{selected_session}.csv")

            if not filtered.empty:
                st.subheader("📈 AI Summary")
                summary = {
                    "Average Club Speed (mph)": round(filtered['Club Speed'].mean(), 2),
                    "Average Ball Speed (mph)": round(filtered['Ball Speed'].mean(), 2),
                    "Average Smash Factor": round(filtered['Smash Factor'].mean(), 2),
                    "Average Launch Angle (deg)": round(filtered['Launch Angle'].mean(), 2),
                    "Average Backspin (rpm)": round(filtered['Backspin'].mean(), 2),
                    "Total Shots": len(filtered)
                }
                st.json(summary)

                # Charts
                st.subheader("📊 Visual Insights")

                chart_data = filtered[["Ball Speed", "Club Speed", "Launch Angle", "Backspin"]].dropna()
                if not chart_data.empty:
                    for col in chart_data.columns:
                        st.altair_chart(
                            alt.Chart(filtered.dropna(subset=[col])).mark_line(point=True).encode(
                                x=alt.X(filtered.dropna(subset=[col]).index.name or "index", title="Shot Number"),
                                y=alt.Y(col, title=col),
                                tooltip=[col]
                            ).interactive().properties(title=f"{col} Over Shots", width=700),
                            use_container_width=True
                        )
            else:
                st.warning("Not enough data for summary.")
