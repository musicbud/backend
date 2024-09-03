from django.urls import re_path
from .consumers import YourConsumer

websocket_urlpatterns = [
    re_path(r'ws/some_path/$', YourConsumer.as_asgi()),
]
