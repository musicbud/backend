from django.urls import path
from channels.routing import URLRouter
from app.consumers import LoginConsumer, GetProfileConsumer

websocket_urlpatterns = [
    path('ws/login/', LoginConsumer.as_asgi()),
    path('ws/me/profile/', GetProfileConsumer.as_asgi()),
]
