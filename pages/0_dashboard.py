import streamlit as st
import pandas as pd
import numpy as np
import openai
import plotly.express as px

st.set_page_config(layout="centered")
st.header("📊 Dashboard – Club Summary")

# CSS for compact tables
st.markdown("""
    <style>
        .dataframe {font-size: small; overflow-x: auto;}
    </style>
""", unsafe_allow_html=True)

# Consistent sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", ["🏠 Home (Upload CSVs)", "📋 Sessions Viewer", "📊 Dashboard"])

if page == "🏠 Home (Upload CSVs)":
    st.switch_page("app.py")
elif page == "📋 Sessions Viewer":
    st.switch_page("pages/1_Sessions_Viewer.py")

# Conditional guidance
if 'df_all' not in st.session_state or st.session_state['df_all'].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    st.subheader("Averages per Club")
    numeric_cols = ['Carry', 'Backspin', 'Sidespin', 'Total', 'Smash Factor', 'Apex Height', 'Launch Angle', 'Attack Angle']
    df_all = df_all.copy()
    
    for col in numeric_cols:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
    
    df_all = df_all.dropna(subset=numeric_cols, how='any')
    
    sessions = st.multiselect("Select Sessions", df_all['Session'].unique(), default=df_all['Session'].unique(), help="Sessions are created per day from uploaded CSVs.")
    clubs = st.multiselect("Select Clubs", df_all['Club'].unique(), default=df_all['Club'].unique())
    filtered = df_all[df_all['Session'].isin(sessions) & df_all['Club'].isin(clubs)] if sessions and clubs else df_all
    
    if filtered[numeric_cols].dtypes.any() == 'object':
        st.warning("One or more numeric columns contain non-numeric data. Aggregates may be incomplete.")
        st.write("Column dtypes:", filtered[numeric_cols].dtypes)
    
    remove_outliers_iqr = st.checkbox("Remove Outliers (based on Carry IQR per club)", value=False)
    remove_contact_outliers = st.checkbox("Remove Fat/Thin Shots (based on Smash Factor, Launch Angle, Backspin, Attack Angle)", value=False)
    
    if remove_outliers_iqr:
        def remove_carry_outliers(group):
            if len(group) < 3:
                return group
            Q1 = group['Carry'].quantile(0.25)
            Q3 = group['Carry'].quantile(0.75)
            IQR = Q3 - Q1
            filtered_group = group[(group['Carry'] >= Q1 - 1.5 * IQR) & (group['Carry'] <= Q3 + 1.5 * IQR)]
            return filtered_group if not filtered_group.empty else group
        
        filtered = filtered.groupby('Club').apply(remove_carry_outliers).reset_index(drop=True)
        st.info("Outliers removed using IQR on Carry distance per club (e.g., excluding poor shots like 100-yard drivers).")
    
    if remove_contact_outliers:
        def is_poor_contact(row):
            club = row['Club']
            smash = row['Smash Factor']
            launch = row['Launch Angle']
            backspin = row['Backspin']
            attack = row['Attack Angle']
            
            if 'Driver' in club:
                return smash < 1.4 or launch < 8 or launch > 16 or backspin < 1500 or backspin > 3500 or attack < -2 or attack > 5
            elif 'Iron' in club:
                return smash < 1.3 or launch < 10 or launch > 22 or backspin < 4000 or backspin > 9000 or attack < -5 or attack > 0
            elif 'Wedge' in club:
                return smash < 1.2 or launch < 25 or launch > 45 or backspin < 6000 or backspin > 12000 or attack < -6 or attack > -2
            else:
                return False
        
        filtered = filtered[~filtered.apply(is_poor_contact, axis=1)]
        st.info("Fat/thin shots removed using thresholds on Smash Factor (poor contact), Launch Angle (high/low), Backspin (extreme), and Attack Angle (too negative for fat). Thresholds are club-specific.")

    grouped = filtered.groupby('Club')[numeric_cols].agg(['mean', 'median', 'std']).round(1)
    
    grouped_flat = grouped.copy()
    grouped_flat.columns = [f"{col[0]}_{col[1]}" for col in grouped_flat.columns]
    grouped_flat = grouped_flat.reset_index()
    
    st.dataframe(grouped_flat, use_container_width=True)
    
    st.markdown("""
    ### Statistic Explanations
    - **Mean**: <span title="Average performance; e.g., mean Carry shows typical distance—aim to increase for better range.">The average value</span>.
    - **Median**: <span title="Middle value, less affected by poor shots; compare to mean to spot extremes.">The middle value</span>.
    - **Std**: <span title="Variability; low std = consistent shots (e.g., Carry std <10 yards is tight grouping).">Measures spread</span>.
    """, unsafe_allow_html=True)
    
    if not grouped_flat.empty:
        metric = st.selectbox("Select Metric for Chart", numeric_cols, index=0)
        chart_data = grouped_flat[['Club', f'{metric}_mean', f'{metric}_median', f'{metric}_std']]
        chart_data = chart_data.melt(id_vars=['Club'], value_vars=[f'{metric}_mean', f'{metric}_median'], var_name='Stat', value_name='Value')
        chart_data['Std'] = chart_data.apply(lambda row: grouped_flat.loc[grouped_flat['Club'] == row['Club'], f'{metric}_std'].values[0] if row['Stat'] == f'{metric}_mean' else 0, axis=1)
        
        fig = px.bar(chart_data, x='Club', y='Value', color='Stat', barmode='group',
                     error_y='Std' if 'Std' in chart_data.columns else None,
                     title=f'{metric}: Mean and Median with Std Deviation')
        fig.update_layout(yaxis_title=metric, hovermode="x")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("AI Insights")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    if api_key and st.button("Generate AI Insights"):
        try:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"Based on these golf shot averages per club (mean, median, std for Carry, Backspin, Sidespin, Total, Smash Factor, Apex Height, Launch Angle, Attack Angle):\n{grouped.to_string()}\nProvide suggestions, comments, and recommendations for improving performance. Focus on fat/thin shots (low Smash Factor, extreme Launch Angle/Backspin), outliers, consistency, and typical golf benchmarks (e.g., driver carry >200 yards, irons Smash Factor >1.3)."
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a golf performance analyst."}, {"role": "user", "content": prompt}]
            )
            insights = response.choices[0].message.content
            st.write(insights)
        except Exception as e:
            st.error(f"Error generating insights: {str(e)}. Check your API key or try again. If quota exceeded, upgrade your OpenAI plan at https://platform.openai.com/account/billing or wait for reset.")
    elif not api_key:
        st.info("Enter your OpenAI API key above to generate AI-powered suggestions on your data (e.g., 'Improve driver smash factor for better distance'). Get a key at openai.com.")
