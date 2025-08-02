# Garmin R10 Multi-Session Analyzer

![Garmin R10 Analyzer](https://img.shields.io/badge/Garmin%20R10-Analyzer-green)  
A Streamlit web app to upload, view, and analyze golf shot data from Garmin R10 launch monitor CSV files.

## Features
- **Home Page**: Upload CSVs, preview data, download processed file, see quick metrics (e.g., average carry).
- **Sessions Viewer**: View the full processed dataset.
- **Dashboard**: Analyze mean, median, and standard deviation per club, filter by session or club, view a carry distance chart, remove outliers (e.g., poor shots via IQR on carry), and generate AI insights using OpenAI API.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/hislopkent/GarminR10Analyzer.git
   cd GarminR10Analyzer
