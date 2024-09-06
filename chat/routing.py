from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path, path
from . import consumers
from django.core.asgi import get_asgi_application

import logging

# Use a function to delay import of consumers
def get_websocket_urlpatterns():
    return [
        re_path(r'ws/chat/(?P<room_name>[\w\s]+)/$', consumers.ChatConsumer.as_asgi()),
        re_path(r'ws/chat/user/(?P<user_username>\w+)/(?P<other_username>\w+)/$', consumers.UserChatConsumer.as_asgi()),
        # Remove the log_and_route wrapper if it's not needed
        # re_path(r'ws/chat/(?P<room_name>\w+)/$', log_and_route('ws/chat/<room_name>/', consumers.ChatConsumer)),
    ]

# Remove this line as it's redundant
# from .consumers import ChatConsumer

# Use this function to load patterns when Django is ready
def load_websocket_urlpatterns():
    global websocket_urlpatterns
    websocket_urlpatterns = get_websocket_urlpatterns()

# Initialize websocket_urlpatterns
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>[\w\s]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chat/user/(?P<user_username>\w+)/(?P<other_username>\w+)/$', consumers.UserChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

def log_and_route(path, consumer):
    def wrapper(scope):
        logger = logging.getLogger(__name__)
        logger.debug(f"Routing websocket connection for path: {path}")
        return consumer.as_asgi()(scope)
    return wrapper
