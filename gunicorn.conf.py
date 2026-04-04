# gunicorn.conf.py

# Number of worker processes
workers = 2

# Worker class for FastAPI (ASGI)
worker_class = "uvicorn.workers.UvicornWorker"

# Bind address
bind = "127.0.0.1:8000"

# Use uvloop (faster event loop)
asgi_loop = "uvloop"

# Access log settings
accesslog = "-"  # log to stdout
access_log_format = '%(h)s - "%(r)s" %(s)s'