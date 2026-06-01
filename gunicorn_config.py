import os
import multiprocessing

# Server socket
bind = f"{os.getenv('APP_HOST', '0.0.0.0')}:{os.getenv('APP_PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging — use stdout/stderr instead of files (Docker captures these)
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'material-management-api'

# Server mechanics
daemon = False
pidfile = '/var/run/gunicorn.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Application
raw_env = [
    'APP_ENV=production'
]
