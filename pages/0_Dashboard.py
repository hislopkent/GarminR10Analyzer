import streamlit as st
import pandas as pd
import numpy as np
import openai
import plotly.express as px
import plotly.graph_objects as go
import os

from utils.sidebar import render_sidebar
from utils.ai_feedback import generate_ai_summary

st.set_page_config(layout="centered")
st.header("📊 Dashboard – Club Summary")

# CSS for compact tables and improved layout
st.markdown(
    """
    <style>
        .dataframe {font-size: small; overflow-x: auto; border: 1px solid #ddd; border-radius: 5px;}
        .sidebar .sidebar-content {background-color: #f0f2f6; padding: 10px;}
        .sidebar a {color: #2ca02c; text-decoration: none; display: block; padding: 5px;}
        .sidebar a:hover {background-color: #228B22; color: white; text-decoration: none; border-radius: 3px;}
        .stExpander > div {border: 1px solid #ddd; border-radius: 5px;}
    </style>
""",
    unsafe_allow_html=True,
)

render_sidebar()

# Conditional guidance
if "df_all" not in st.session_state or st.session_state["df_all"].empty:
    st.sidebar.warning("Upload data to enable all features.")
else:
    st.sidebar.success("Data loaded. Explore sessions or dashboard!")

df_all = st.session_state.get('df_all')

if df_all is None or df_all.empty:
    st.warning("No session data uploaded yet. Go to the Home page to upload.")
else:
    with st.expander("📋 Filters", expanded=True):
        st.subheader("Averages per Club")
        numeric_cols = ['Carry', 'Backspin', 'Sidespin', 'Total', 'Smash Factor', 'Apex Height', 'Launch Angle', 'Attack Angle']
        df_all = df_all.copy()
        
        for col in numeric_cols:
            if col in df_all.columns:
                df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
        
        df_all = df_all.dropna(subset=numeric_cols, how='any')
        
        session_options = ['All Sessions'] + sorted(df_all['Session'].unique())
        selected_session = st.selectbox(
            "Select Session",
            session_options,
            help="Sessions are automatically labeled by date. Choose one to view or select 'All Sessions'."
        )
        clubs = st.multiselect("Select Clubs", df_all['Club'].unique(), default=df_all['Club'].unique())

        if selected_session != 'All Sessions':
            filtered = df_all[df_all['Session'] == selected_session]
        else:
            filtered = df_all

        if clubs:
            filtered = filtered[filtered['Club'].isin(clubs)]
        
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
            st.info("Outliers removed using IQR on Carry distance per club.")
        
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
            st.info("Fat/thin shots removed using thresholds on Smash Factor, Launch Angle, Backspin, and Attack Angle.")

    @st.cache_data
    def compute_grouped(filtered):
        return filtered.groupby('Club')[numeric_cols].agg(['mean', 'median', 'std']).round(1)

    grouped = compute_grouped(filtered)
    
    grouped_flat = grouped.copy()
    grouped_flat.columns = [f"{col[0]}_{col[1]}" for col in grouped_flat.columns]
    grouped_flat = grouped_flat.reset_index()
    
    # Styled table with tooltips and reduced decimals
    def highlight_metrics(s):
        color = 'white'
        tooltip = ''
        if s.name == 'Carry_mean':
            tooltip = "Target: >220 yds (Driver), >150 yds (7 Iron)"
            return ['background-color: red' if v < 150 else 'background-color: green' for v in s]
        elif s.name == 'Sidespin_mean':
            tooltip = "Target: <500 rpm for consistency"
            return ['background-color: red' if abs(v) > 500 else 'background-color: green' for v in s]
        elif s.name == 'Smash Factor_mean':
            tooltip = "Target: >1.45 (Driver), >1.3 (Irons)"
            return ['background-color: red' if v < 1.3 else 'background-color: green' for v in s]
        elif s.name == 'Launch Angle_mean':
            tooltip = "Target: 10-16° (Driver), 15-20° (7 Iron)"
            clubs = grouped_flat.loc[s.index, 'Club']
            styles = []
            for v, club in zip(s, clubs):
                if 'Driver' in club:
                    styles.append('background-color: red' if (v < 10 or v > 16) else 'background-color: green')
                elif '7 Iron' in club or 'Iron' in club:
                    styles.append('background-color: red' if (v < 15 or v > 20) else 'background-color: green')
                else:
                    styles.append('background-color: green')
            return styles
        elif s.name == 'Apex Height_mean':
            tooltip = "Target: 30-40 ft (Driver), 60-90 ft (Irons)"
            return ['background-color: red' if v < 30 or v > 40 else 'background-color: green' for v in s]
        elif s.name == 'Backspin_mean':
            tooltip = "Target: 1500-3500 rpm (Driver), 5000-7000 rpm (7 Iron)"
            return ['background-color: red' if v < 1500 or v > 3500 else 'background-color: green' for v in s]
        return [f'background-color: {color}; title: "{tooltip}"' for _ in s]

    styled_table = grouped_flat.style.apply(
        highlight_metrics,
        subset=[
            f"{metric}_mean" for metric in [
                "Carry",
                "Sidespin",
                "Smash Factor",
                "Launch Angle",
                "Apex Height",
                "Backspin",
            ]
        ],
    )

    # Only format numeric columns to avoid ValueError on string columns like 'Club'
    numeric_columns = grouped_flat.select_dtypes(include="number").columns
    format_dict = {col: "{:.1f}" for col in numeric_columns}
    styled_table = styled_table.format(format_dict)  # Reduce decimals to 1
    st.dataframe(styled_table, use_container_width=True)

    # Summary Metrics
    with st.expander("📊 Summary Metrics", expanded=True):
        for club in grouped_flat['Club']:
            club_data = grouped_flat[grouped_flat['Club'] == club].iloc[0]
            carry_mean = club_data['Carry_mean']
            smash_mean = club_data['Smash Factor_mean']
            launch_mean = club_data['Launch Angle_mean']
            backspin_mean = club_data['Backspin_mean']
            st.metric(f"Carry ({club})", f"{carry_mean:.1f} yds", 
                     delta=f"{'🟢' if carry_mean >= 220 else '🟠'} {max(0, 220 - carry_mean):.1f} yds to 220" if 'Driver' in club else 
                           f"{'🟢' if carry_mean >= 150 else '🟠'} {max(0, 150 - carry_mean):.1f} yds to 150" if '7 Iron' in club else "",
                     delta_color="inverse")
            st.metric(f"Smash Factor ({club})", f"{smash_mean:.1f}", 
                     delta=f"{'🟢' if smash_mean >= 1.45 else '🟠'} {max(0, 1.45 - smash_mean):.1f} to 1.45" if 'Driver' in club else 
                           f"{'🟢' if smash_mean >= 1.3 else '🟠'} {max(0, 1.3 - smash_mean):.1f} to 1.3" if 'Iron' in club else "",
                     delta_color="inverse")
            st.metric(f"Launch Angle ({club})", f"{launch_mean:.1f}°", 
                     delta=f"{'🟢' if 10 <= launch_mean <= 16 else '🟠'} {min(abs(10 - launch_mean), abs(16 - launch_mean)):.1f}° to 10-16°" if 'Driver' in club else 
                           f"{'🟢' if 15 <= launch_mean <= 20 else '🟠'} {min(abs(15 - launch_mean), abs(20 - launch_mean)):.1f}° to 15-20°" if '7 Iron' in club else "",
                     delta_color="inverse")
            st.metric(f"Backspin ({club})", f"{backspin_mean:.1f} rpm", 
                     delta=f"{'🟢' if 1500 <= backspin_mean <= 3500 else '🟠'} {min(abs(1500 - backspin_mean), abs(3500 - backspin_mean)):.1f} rpm to 1500-3500" if 'Driver' in club else 
                           f"{'🟢' if 5000 <= backspin_mean <= 7000 else '🟠'} {min(abs(5000 - backspin_mean), abs(7000 - backspin_mean)):.1f} rpm to 5000-7000" if '7 Iron' in club else "",
                     delta_color="inverse")

    st.markdown("""
    ### Statistics Explanations
    - **Mean**: Average performance; e.g., mean Carry is your typical distance (aim >220 yds for Driver).
    - **Median**: Middle value, less affected by outliers; compare to mean for consistency.
    - **Std**: Variability; lower values (e.g., <10% of mean) indicate consistent shots.
    Color coding: Green = within benchmarks, Red = outside (customize via filters).
    """, unsafe_allow_html=True)

    if not grouped_flat.empty:
        metric = st.selectbox("Select Metric for Chart", numeric_cols, index=0)
        chart_data = grouped_flat[['Club', f'{metric}_mean', f'{metric}_median', f'{metric}_std']]
        chart_data = chart_data.melt(id_vars=['Club'], value_vars=[f'{metric}_mean', f'{metric}_median'], var_name='Stat', value_name='Value')
        chart_data['Std'] = chart_data.apply(lambda row: grouped_flat.loc[grouped_flat['Club'] == row['Club'], f'{metric}_std'].values[0] if row['Stat'] == f'{metric}_mean' else 0, axis=1)
        chart_data['Value'] = chart_data['Value'].round(1)  # Reduce decimals
        
        fig = px.bar(chart_data, x='Club', y='Value', color='Stat', barmode='group',
                     error_y='Std' if 'Std' in chart_data.columns else None,
                     title=f'{metric}: Mean and Median with Std Deviation',
                     hover_data=['Std'])
        fig.update_layout(yaxis_title=metric, hovermode="x", yaxis_tickformat=".1f", legend_title_text='Statistic')
        st.plotly_chart(fig, use_container_width=True)

        lateral_col = next((col for col in ['Offline', 'Side', 'Deviation', 'Lateral', 'Sidespin'] if col in filtered.columns), None)
        if lateral_col:
            st.subheader("Shot Dispersion by Club")

            def std_ellipse(x, y, n_std=1.0, num_points=100):
                if len(x) < 2:
                    return None, None
                cov = np.cov(x, y)
                if np.linalg.det(cov) == 0:
                    return None, None
                eigvals, eigvecs = np.linalg.eigh(cov)
                order = eigvals.argsort()[::-1]
                eigvals, eigvecs = eigvals[order], eigvecs[:, order]
                theta = np.linspace(0, 2 * np.pi, num_points)
                ellipse = np.array([
                    np.sqrt(eigvals[0]) * np.cos(theta),
                    np.sqrt(eigvals[1]) * np.sin(theta),
                ])
                transform = eigvecs @ ellipse
                center = [np.mean(x), np.mean(y)]
                xs = center[0] + n_std * transform[0]
                ys = center[1] + n_std * transform[1]
                return xs, ys

            fig_disp = go.Figure()
            colors = px.colors.qualitative.Plotly
            for i, (club, grp) in enumerate(filtered.groupby("Club")):
                color = colors[i % len(colors)]
                fig_disp.add_trace(
                    go.Scatter(
                        x=grp[lateral_col],
                        y=grp['Carry'],
                        mode='markers',
                        name=str(club),
                        marker=dict(color=color)
                    )
                )
                ell_x, ell_y = std_ellipse(grp[lateral_col], grp['Carry'])
                if ell_x is not None:
                    fig_disp.add_trace(
                        go.Scatter(
                            x=ell_x,
                            y=ell_y,
                            mode='lines',
                            showlegend=False,
                            line=dict(color=color)
                        )
                    )
            fig_disp.update_layout(
                title="Shot Dispersion (Carry vs. Lateral)",
                xaxis_title=lateral_col,
                yaxis_title='Carry'
            )
            st.plotly_chart(fig_disp, use_container_width=True)
        else:
            st.info("No lateral dispersion data available to plot.")

    st.markdown("---")
    show_ai_feedback = st.checkbox("\U0001F4A1 Show AI Summary Under Each Club", value=False)
    if show_ai_feedback:
        st.info("Generating personalized feedback per club based on your session data...")

    for club in sorted(filtered["Club"].unique()):
        st.subheader(f"\U0001F50E {club}")
        club_df = filtered[filtered["Club"] == club]
        club_stats = club_df.describe(include="all").T
        numeric_cols = club_stats.select_dtypes(include="number").columns
        st.dataframe(club_stats.style.format("{:.1f}", subset=numeric_cols))
        if show_ai_feedback:
            with st.spinner(f"Analyzing {club}..."):
                feedback = generate_ai_summary(club, filtered)
                st.markdown(f"**AI Feedback:**\n\n> {feedback}")

    with st.expander("💡 Show AI Suggestions", expanded=False):
        st.subheader("AI Insights")
        enable_ai = st.checkbox("Enable AI Insights")
        if enable_ai:
            focus = st.text_input("AI Focus (e.g., 'irons only' or 'distance improvement')", "")
            api_key = os.getenv("OPENAI_API_KEY")
            assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
            if not api_key or not assistant_id:
                st.warning("OpenAI API Key or Assistant ID not set in Render environment variables. Set OPENAI_API_KEY and OPENAI_ASSISTANT_ID in your Render dashboard.")
            elif st.button("Generate AI Insights"):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    thread = client.beta.threads.create()
                    data_str = filtered.to_string() if len(filtered) < 200 else filtered.sample(200).to_string()
                    prompt = f"Full filtered shot data:\n{data_str}\nAggregated averages per club (mean, median, std for Carry, Backspin, Sidespin, Total, Smash Factor, Apex Height, Launch Angle, Attack Angle):\n{grouped.to_string()}\nCompare each club’s average to common benchmarks for a 15–20 handicap player (e.g., Driver Carry >220 yds, Smash Factor >1.45, Launch Angle 10-16°; 7 Iron Carry >150 yds, Smash Factor >1.3, Launch Angle 15-20°). Provide per-club suggestions, comments, and recommendations for improving performance. Focus on {focus if focus else 'general'} aspects like fat/thin shots (low Smash Factor, extreme Launch Angle/Backspin), outliers, consistency, and typical golf benchmarks."
                    message = client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=prompt
                    )
                    run = client.beta.threads.runs.create(
                        thread_id=thread.id,
                        assistant_id=assistant_id
                    )
                    import time
                    while run.status != "completed":
                        time.sleep(1)
                        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    insights = messages.data[0].content[0].text.value
                    st.write(insights)
                except Exception as e:
                    st.error(f"Error generating insights: {str(e)}. Check environment variables or try again. If quota exceeded, upgrade your OpenAI plan at https://platform.openai.com/account/billing or wait for reset.")

    with st.expander("📌 Benchmark Insights"):
        st.subheader("Reference Benchmarks (Jon Sherman Style)")
        benchmarks = pd.DataFrame({
            "Metric": ["Carry", "Smash Factor", "Launch Angle", "Backspin", "Std Dev (Carry)"],
            "Driver": [">220 yds", ">1.45", "10°–16°", "1500–3500 rpm", "<10% of mean"],
            "7 Iron": [">150 yds", ">1.30", "15°–20°", "5000–7000 rpm", "<10% of mean"],
            "PW": ["", ">1.25", "25°–45°", "8000–11000 rpm", "<10% of mean"],
            "Notes": ["Scoring consistency", "Energy transfer", "Optimized flight", "Predictability", "Consistency"]
        })
        st.table(benchmarks)

    st.subheader("📌 Coaching Summary (Sherman Style)")
    st.markdown("""
    - Prioritize **Driver contact quality** — low Smash or high Launch = center-face issues.
    - If **Backspin** is erratic, you're likely mis-hitting or swinging inconsistently.
    - Use your **7 Iron carry and dispersion** as a litmus test — Jon calls this a "benchmark club".
    - Focus practice on clubs or metrics showing ❌ in benchmarks — they represent scoring leaks.
    """)
