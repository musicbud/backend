import os
import multiprocessing
import logging
from gunicorn import glogging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musicbud.settings")

bind = "127.0.0.1:8000"
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1

worker_class = "uvicorn.workers.UvicornWorker"

# Modify these lines for better logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Custom logging class to avoid reentrant calls
class CustomLogger(glogging.Logger):
    def setup(self, cfg):
        super().setup(cfg)
        # Remove default handlers
        self.error_log.handlers = []
        self.access_log.handlers = []
        
        # Add custom handler
        handler = logging.StreamHandler()
        self.error_log.addHandler(handler)
        self.access_log.addHandler(handler)

logger_class = CustomLogger
