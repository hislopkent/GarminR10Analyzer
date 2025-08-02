
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Garmin R10 Multi-Session Analyzer with AI Summaries", layout="wide")

st.title("📊 Garmin R10 Multi-Session Analyzer with AI Summaries")

uploaded_files = st.file_uploader("Upload one or more Garmin R10 CSV files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        if "Club Type" in df.columns:
            df.rename(columns={"Club Type": "Club"}, inplace=True)
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    if "Date" in df_all.columns:
        df_all["Session"] = pd.to_datetime(df_all["Date"]).dt.strftime("%Y-%m-%d %H:%M")
    else:
        df_all["Session"] = "Unknown"

    sessions = sorted(df_all["Session"].unique())
    selected_session = st.selectbox("Filter by session", ["All Sessions"] + sessions)

    clubs = sorted(df_all["Club"].dropna().astype(str).unique())
    selected_club = st.selectbox("Select a club", clubs)

    if selected_session != "All Sessions":
        df_all = df_all[df_all["Session"] == selected_session]

    filtered = df_all[df_all["Club"].astype(str) == selected_club]

    st.subheader(f"Raw data for {selected_club}")
    st.dataframe(filtered)

    if not filtered.empty:
        with st.expander("📈 Charts & Visuals"):
            st.altair_chart(
                alt.Chart(filtered).mark_bar().encode(
                    x=alt.X("Club Speed", bin=alt.Bin(maxbins=30)),
                    y='count()',
                    tooltip=["Club Speed"]
                ).properties(title="Club Speed Distribution"),
                use_container_width=True
            )

        st.download_button("Download filtered data as CSV", data=filtered.to_csv(index=False), file_name="filtered_data.csv", mime="text/csv")

        st.subheader("🧠 AI Summary")
        avg_speed = filtered["Club Speed"].mean()
        avg_path = filtered["Club Path"].mean()
        avg_attack = filtered["Attack Angle"].mean()
        summary = f"Average club speed: {avg_speed:.2f} mph, path: {avg_path:.2f}°, attack angle: {avg_attack:.2f}°"
        st.write(summary)
    else:
        st.warning("No data available for the selected club.")
else:
    st.info("Please upload one or more Garmin R10 CSV files.")
