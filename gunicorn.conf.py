import os

bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
timeout = 2400  # 40 minutes
keepalive = 300
max_requests = 1000
preload_app = True