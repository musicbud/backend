command = '/home/ubuntu/musicbud/myenv/bin/gunicorn'
pythonpath = '/home/mahmoud/Documents/GitHub/musicbud-revanced'
bind = '127.0.0.1:8000'
workers = 1
worker_class = 'uvicorn.workers.UvicornWorker'
django_settings = 'musicbud.settings'

# gunicorn myproject.asgi:application --config gunicorn.conf.py
