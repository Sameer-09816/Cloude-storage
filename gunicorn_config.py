# Gunicorn configuration for ultra-fast video streaming
# Optimized for VPS with 4 CPU cores and 8GB RAM
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes - Optimized for 4 CPU cores
workers = 8  # 2 * CPU cores for I/O bound operations (video streaming)
worker_class = "gthread"  # Use threaded workers for better concurrency
threads = 4  # 4 threads per worker (total 32 concurrent threads)
worker_connections = 1000
timeout = 300  # Increased timeout for large file operations
keepalive = 10  # Longer keepalive for persistent connections

# Process naming
proc_name = 'cloud-storage'

# Logging
accesslog = '/var/log/cloud-storage/access.log'
errorlog = '/var/log/cloud-storage/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False  # Don't daemonize (systemd will handle this)
pidfile = '/var/run/cloud-storage.pid'
umask = 0
user = None
group = None
tmp_upload_dir = '/tmp'

# Performance optimizations
max_requests = 10000  # Restart workers after 10k requests to prevent memory leaks
max_requests_jitter = 1000  # Add some randomness to prevent all workers restarting at once
preload_app = False  # Don't preload (better for video streaming)

# SSL (if needed)
# keyfile = '/etc/ssl/private/key.pem'
# certfile = '/etc/ssl/certs/cert.pem'

# Server hooks
def on_starting(server):
    print("Gunicorn master starting - Optimized for video streaming")

def on_reload(server):
    print("Gunicorn master reloading")

def when_ready(server):
    print("Gunicorn is ready. Spawning workers")
    print(f"Workers: {workers}, Threads per worker: {threads}")
    print(f"Total concurrent threads: {workers * threads}")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    print(f"Worker spawned (pid: {worker.pid})")

def post_worker_init(worker):
    print(f"Worker initialized (pid: {worker.pid})")

def worker_int(worker):
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    print(f"Worker received SIGABRT signal (pid: {worker.pid})")
