# Garmin R10 Analyzer 📊

A Streamlit-based app for analyzing and improving your golf performance using data from the Garmin R10 launch monitor. Inspired by Jon Sherman’s *Four Foundations of Golf*, this tool gives personalized insights, outlier filtering, club benchmarks, and smart summaries.

---

## 🚀 Features

### 📁 Multi-Session Data Upload
- Upload multiple Garmin R10 CSV files
- Automatically groups data by session and club

### 📊 Dashboard View
- Aggregates club data (Carry, Smash Factor, Launch Angle, etc.)
- Optional filters to remove outliers or poor contact shots
- Interactive Plotly charts (Mean vs. Median vs. Std Dev)
- Smart session and club filtering

### ✅ Benchmark Report (NEW)
- Compares your stats to Jon Sherman–style benchmarks
- Per-club report cards with ✅ / ❌ ratings
- Built-in feedback for practice priorities

### 🧠 AI Insights (Optional)
- Requires `OPENAI_API_KEY` and `OPENAI_ASSISTANT_ID` environment variables
- Generates coaching-style analysis and per-club summaries

---

## 📂 File Structure

```
GarminR10Analyzer-main/
├── app.py                      # Main entry point (CSV uploads, session state)
├── pages/
│   ├── 0_Dashboard.py          # Club averages + filters
│   ├── 1_Sessions_Viewer.py    # Table viewer for all shots
│   └── 2_Benchmark_Report.py   # 🔥 Benchmark coaching report
├── utils/
│   └── benchmarks.py           # Performance goals and evaluator
├── requirements.txt            # Dependencies
├── Dockerfile + render.yaml    # Render.com deployment
```

---

## 🛠 Setup Instructions

### 🧪 Local Run

```bash
git clone https://github.com/hislopkent/GarminR10Analyzer.git
cd GarminR10Analyzer
pip install -r requirements.txt
streamlit run app.py
```

### ☁️ Deploy to Render
1. Add `PASSWORD` as environment variable
2. Deploy using `render.yaml` + Dockerfile
3. Upload your CSV files to begin

---

## 📥 Garmin CSV Format

Ensure your CSV contains these columns (from Garmin R10 export):
- `Date`, `Club Type`, `Carry Distance`, `Total Distance`
- `Smash Factor`, `Backspin`, `Launch Angle`, etc.

---

## 📚 Inspired By

- [Jon Sherman – Practical Golf](https://practical-golf.com)
- *The Four Foundations of Golf*
- ShotMetrics-style coaching summaries
