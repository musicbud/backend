from celery import shared_task
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')
@shared_task
def long_running_task():
    # Your long-running task logic here
    pass
