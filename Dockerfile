
FROM python:3.11-slim

WORKDIR /app

# Copy only requirements first to leverage Docker layer caching and
# avoid potential lease issues when installing dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code in a separate step.
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
