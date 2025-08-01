from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "<h2>Garmin R10 AI Stat Analyzer - Preview Build</h2><p>Upload coming soon</p>"