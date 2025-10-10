import json
import os
from datetime import datetime
from pathlib import Path

class JobStore:
    def __init__(self):
        self.jobs_file = "/home/site/wwwroot/jobs.json"
        self.jobs = self._load_jobs()
    
    def _load_jobs(self):
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_jobs(self):
        with open(self.jobs_file, 'w') as f:
            json.dump(self.jobs, f)
    
    def create_job(self, job_id, filename):
        self.jobs[job_id] = {
            "id": job_id,
            "filename": filename,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "result_file": None,
            "error": None
        }
        self._save_jobs()
    
    def update_job(self, job_id, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
            self._save_jobs()
    
    def get_job(self, job_id):
        return self.jobs.get(job_id)
    
    def get_active_jobs(self):
        return [job for job in self.jobs.values() if job['status'] == 'processing']

job_store = JobStore()