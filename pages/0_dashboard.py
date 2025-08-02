import streamlit as st
import pandas as pd
import numpy as np
import openai

st.set_page_config(layout="centered")
st.header("📊 Dashboard – Club Summary")

# CSS for compact tables
st.markdown("""<style>.dataframe {font-size: small; overflow-x: auto;}</style>""", unsafe_allow_html=True)

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
    if st.button("Go to Home (Upload)"):
        st.switch_page("app.py")
else:
    st.subheader("Averages per Club")
    numeric_cols = ['Carry', 'Backspin', 'Sidespin', 'Total', 'Smash Factor', 'Apex Height']
    df_all = df_all.copy()
    df_all = df_all.replace([np.inf, -np.inf], np.nan).dropna(subset=numeric_cols, how='any')
    
    # Session and club filters
    sessions = st.multiselect("Select Sessions", df_all['Session'].unique(), default=df_all['Session'].unique())
    clubs = st.multiselect("Select Clubs", df_all['Club'].unique(), default=df_all['Club'].unique())
    filtered = df_all[df_all['Session'].isin(sessions) & df_all['Club'].isin(clubs)] if sessions and clubs else df_all
    
    # Outlier removal option
    remove_outliers = st.checkbox("Remove Outliers (based on Carry IQR per club)", value=False)
    if remove_outliers:
        def remove_carry_outliers(group):
            if len(group) < 3:  # Need at least 3 shots for IQR
                return group
            Q1 = group['Carry'].quantile(0.25)
            Q3 = group['Carry'].quantile(0.75)
            IQR = Q3 - Q1
            return group[(group['Carry'] >= Q1 - 1.5 * IQR) & (group['Carry'] <= Q3 + 1.5 * IQR)]
        
        filtered = filtered.groupby('Club').apply(remove_carry_outliers).reset_index(drop=True)
        st.info("Outliers removed using IQR on Carry distance per club (e.g., excluding poor shots like 100-yard drivers).")
    
    grouped = filtered.groupby('Club')[numeric_cols].agg(['mean', 'median', 'std']).round(1)
    grouped = grouped.sort_index()
    st.dataframe(grouped, use_container_width=True)
    
    # Bar chart for carry distance
    if st.checkbox("Show Carry Distance Chart", value=True):
        carry_data = grouped[('Carry', 'mean')].reset_index()
        chart_data = {
            "type": "bar",
            "data": {
                "labels": carry_data['Club'].tolist(),
                "datasets": [{
                    "label": "Average Carry Distance",
                    "data": carry_data[('Carry', 'mean')].tolist(),
                    "backgroundColor": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
                    "borderColor": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
                    "borderWidth": 1
                }]
            },
            "options": {
                "scales": {
                    "y": {"title": {"display": True, "text": "Yards"}}
                }
            }
        }
        st.markdown("### Average Carry Distance by Club")
        st.components.v1.html(f"""
            <canvas id='carryChart'></canvas>
            <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
            <script>
                const ctx = document.getElementById('carryChart').getContext('2d');
                new Chart(ctx, {chart_data});
            </script>
        """, height=400)
    
    # AI Insights section
    st.subheader("AI Insights")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    if api_key and st.button("Generate AI Insights"):
        try:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"Based on these golf shot averages per club (mean, median, std for Carry, Backspin, Sidespin, Total, Smash Factor, Apex Height):\n{grouped.to_string()}\nProvide suggestions, comments, and recommendations for improving performance. Focus on outliers, consistency, and typical golf benchmarks (e.g., driver carry >200 yards)."
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a golf performance analyst."}, {"role": "user", "content": prompt}]
            )
            insights = response.choices[0].message.content
            st.write(insights)
        except Exception as e:
            st.error(f"Error generating insights: {str(e)}. Check your API key or try again.")
    elif not api_key:
        st.info("Enter your OpenAI API key above to generate AI-powered suggestions on your data (e.g., 'Improve driver smash factor for better distance'). Get a key at openai.com.")
