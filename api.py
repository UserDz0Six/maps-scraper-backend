from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import pandas as pd
import os
import json
from datetime import datetime
from scraper import scrape_places, save_places_to_csv
import logging

app = Flask(__name__)
CORS(app)

# Configuration
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Global state for tracking scraping jobs
jobs = {}
job_counter = 0

logging.basicConfig(level=logging.INFO)

def run_scraping_job(job_id: str, search_query: str, total: int):
    """Background task to run the scraping"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        logging.info(f"Starting job {job_id}: {search_query} ({total} results)")
        places = scrape_places(search_query, total)
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, f"{job_id}.csv")
        save_places_to_csv(places, output_file, append=False)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["results_count"] = len(places)
        jobs[job_id]["output_file"] = output_file
        
        logging.info(f"Job {job_id} completed with {len(places)} results")
    except Exception as e:
        logging.error(f"Job {job_id} failed: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "API is running"})

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """Start a new scraping job"""
    global job_counter
    
    data = request.json
    search_query = data.get('search_query', '')
    total = data.get('total', 10)
    
    if not search_query:
        return jsonify({"error": "search_query is required"}), 400
    
    if total < 1 or total > 100:
        return jsonify({"error": "total must be between 1 and 100"}), 400
    
    # Create new job
    job_counter += 1
    job_id = f"job_{job_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    jobs[job_id] = {
        "id": job_id,
        "search_query": search_query,
        "total": total,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "results_count": 0,
        "output_file": None,
        "error": None
    }
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_scraping_job, args=(job_id, search_query, total))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "message": "Scraping job started",
        "status": "pending"
    }), 202

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a specific job"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(jobs[job_id])

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    return jsonify(list(jobs.values()))

@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """Get results of a completed job"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        return jsonify({"error": "Job not completed yet"}), 400
    
    output_file = job.get("output_file")
    if not output_file or not os.path.exists(output_file):
        return jsonify({"error": "Results file not found"}), 404
    
    try:
        df = pd.read_csv(output_file)
        # Replace NaN with None for proper JSON serialization
        df = df.fillna('')  # Replace NaN with empty string for JSON compatibility
        results = df.to_dict(orient='records')
        
        # Convert empty strings back to None for cleaner JSON
        for result in results:
            for key, value in result.items():
                if value == '':
                    result[key] = None
        
        return jsonify({
            "job_id": job_id,
            "count": len(results),
            "data": results
        })
    except Exception as e:
        return jsonify({"error": f"Failed to read results: {str(e)}"}), 500

@app.route('/api/results/<job_id>/download', methods=['GET'])
def download_results(job_id):
    """Download CSV file of results"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        return jsonify({"error": "Job not completed yet"}), 400
    
    output_file = job.get("output_file")
    if not output_file or not os.path.exists(output_file):
        return jsonify({"error": "Results file not found"}), 404
    
    return send_file(output_file, as_attachment=True, download_name=f"{job_id}.csv")

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its results"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    output_file = job.get("output_file")
    
    # Delete CSV file if exists
    if output_file and os.path.exists(output_file):
        os.remove(output_file)
    
    # Remove job from memory
    del jobs[job_id]
    
    return jsonify({"message": "Job deleted successfully"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
