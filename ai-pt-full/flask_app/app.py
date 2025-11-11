from flask import Flask, request, jsonify, render_template, abort
import requests
import uuid
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Assuming the inference script is in the ml folder, and this script is in flask_app
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ml.infer import ModelInference

# --- Flask App Initialization ---
app = Flask(__name__)
inference_engine = ModelInference()

# --- Configuration ---
JOBS_FILE = "../experiments/jobs.json"
AUTH_TOKEN = os.environ.get("AI_PT_AUTH_TOKEN", "your-secret-token") # Use env var or a default


def load_jobs():
    """Loads job history from the JSON file."""
    if not os.path.exists(JOBS_FILE):
        return {}
    with open(JOBS_FILE, 'r') as f:
        return json.load(f)

def save_jobs(jobs):
    """Saves job history to the JSON file."""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)


@app.before_request
def check_auth_token():
    """Checks for a valid auth token on protected routes."""
    if request.path.startswith('/api/'):
        token = request.headers.get('Authorization')
        if token != f"Bearer {AUTH_TOKEN}":
            abort(401, description="Unauthorized: Invalid or missing token.")


@app.route('/')
def dashboard():
    """Renders the main HTML dashboard."""
    jobs = load_jobs()
    return render_template('index.html', jobs=list(jobs.values()))


@app.route('/api/scan', methods=['POST'])
def start_scan():
    """
    API endpoint to start a new scan.
    Accepts a JSON payload with a "target" URL.
    """
    data = request.json
    if not data or 'target' not in data:
        return jsonify({"error": "Target URL is required."}), 400

    target_url = data['target']
    job_id = str(uuid.uuid4())

    jobs = load_jobs()

    try:
        # --- 1. Make a safe GET request ---
        headers = {'User-Agent': 'AI-PT-Scanner/1.0'}
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()

        # --- 2. Extract content ---
        content_type = response.headers.get('Content-Type', '')
        text_content = ""
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            # For simplicity, we use the raw text. A more advanced version might clean this up.
            text_content = soup.get_text(separator=' ', strip=True)
            preview = response.text[:500] # HTML preview
        else:
            text_content = response.text
            preview = text_content[:500] # Raw preview

        # --- 3. Run ML Predictions ---
        # We will use the TF-IDF model for speed in the API
        ml_predictions = inference_engine.predict_tfidf(text_content)

        # --- 4. Store Job ---
        job_result = {
            "job_id": job_id,
            "target": target_url,
            "timestamp": datetime.now().isoformat(),
            "status": "Completed",
            "http_status": response.status_code,
            "headers": dict(response.headers),
            "preview": preview,
            "ml_predictions": ml_predictions
        }
        jobs[job_id] = job_result
        save_jobs(jobs)

        return jsonify(job_result), 200

    except requests.RequestException as e:
        error_message = f"Failed to fetch target: {str(e)}"
        job_result = {
            "job_id": job_id,
            "target": target_url,
            "timestamp": datetime.now().isoformat(),
            "status": "Failed",
            "error": error_message
        }
        jobs[job_id] = job_result
        save_jobs(jobs)
        return jsonify(job_result), 500


@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """Returns the full job history."""
    return jsonify(load_jobs())


if __name__ == '__main__':
    # Create the experiments directory if it doesn't exist
    if not os.path.exists('../experiments'):
        os.makedirs('../experiments')
    app.run(debug=True, port=5000)
