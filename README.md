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

### 📝 Practice Log (NEW)
- Track session notes and completed drills
- Save logs locally and download as CSV

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

### 🐳 Docker Build (Optional)

If you prefer to run the app in a container, build the image with Docker's
cache disabled to avoid occasional `lease <id>: not found` errors from
BuildKit:

```bash
./build.sh
```

This script wraps `docker build --no-cache` so no cached layers are reused
during the build.

### ☁️ Deploy to Render
1. Add `PASSWORD` as environment variable
2. Deploy using `render.yaml` + Dockerfile
3. Upload your CSV files to begin

### 📦 File Upload Limits
- Render limits request bodies to ~100MB. The app caps uploads at 50MB per file to stay under this limit.
- If a file is larger than 50MB, split it before uploading.
- Malformed CSVs are detected and skipped with a clear error message.

---

## 📥 Garmin CSV Format

Ensure your CSV contains these columns (from Garmin R10 export):
- `Date`, `Club Type`, `Carry Distance`, `Total Distance`
- `Smash Factor`, `Backspin`, `Launch Angle`, etc.

---
