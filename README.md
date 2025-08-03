# Garmin R10 Analyzer 📊

A Streamlit-based app for analyzing and improving your golf performance using data from the Garmin R10 launch monitor. Inspired by Jon Sherman’s *Four Foundations of Golf*, this tool gives personalized insights, outlier filtering, club benchmarks, and smart summaries.

---

## 🚀 Features

### 📁 Multi-Session Data Upload
- Upload multiple Garmin R10 CSV files
- Automatically groups data by session and club

### 📈 Analysis Page
- Overview tab summarises averages and consistency by club
- Benchmarking tab explores dispersion and shot-level metrics
- Interactive Plotly charts for carry distance and dispersion
- Smart session and club filtering

### ✅ Benchmark Report (NEW)
- Compares your stats to Jon Sherman–style benchmarks
- Per-club report cards with ✅ / ❌ ratings
- Built-in feedback for practice priorities

### 📋 Sessions Page
- Table viewer for raw shot data
- Built-in practice log to capture notes and drills
- Download logs as CSV

### 🧠 AI Feedback (Optional)
- Requires `OPENAI_API_KEY` and `OPENAI_ASSISTANT_ID` environment variables
- Club insight summaries and session-wide AI analysis

---

## 📂 File Structure

```
GarminR10Analyzer-main/
├── app.py                      # Main entry point (CSV uploads, session state)
├── pages/
│   ├── 0_Analysis.py           # Overview + benchmarking
│   ├── 1_Sessions.py           # Viewer + practice log
│   ├── 2_Benchmark_Report.py   # 🔥 Benchmark coaching report
│   └── 3_AI_Feedback.py        # AI summaries and coaching
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


---
### 🔐 OpenAI API Key Setup
To use the AI Insights feature, set your OpenAI API key as an environment variable:

```
OPENAI_API_KEY=your_key_here
```
This is securely accessed via `os.getenv()`.

---

## 🧑‍💻 Development & Troubleshooting

The codebase is intentionally lightweight so it is easy to extend with new
pages or utilities. A few tips for working on the project:

- **Session state** is managed centrally in `app.py`. Uploaded files and the
  combined dataframe are cached to `sample_data/session_cache.pkl` so that the
  app can recover from reloads. Clearing this file will reset the app's state.
- **Logging** is configured via `utils/logger.py`. Messages are written to
  `app.log` and the log level can be adjusted with the `LOG_LEVEL`
  environment variable.
- **Tests**: run `pytest` to execute unit tests for benchmark calculations and
  drill recommendations. Adding tests for new utilities is encouraged.
- **Pages & utilities**: each Streamlit page lives in the `pages/` directory and
  most shared functionality is in `utils/`. Docstrings throughout the project
  provide context for key functions to make future edits easier.

If something looks off when running locally, start by inspecting the logs and
verifying that your CSV files contain the expected columns.
