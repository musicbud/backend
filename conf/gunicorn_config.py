command = '/home/ubuntu/musicbud/myenv/bin/gunicorn'
pythonpath = '/home/ubuntu/musicbud'
bind ='0.0.0.0:8000'
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"



# gunicorn myproject.asgi:application --config gunicorn.conf.py
