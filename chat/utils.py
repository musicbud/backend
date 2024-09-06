from django.apps import apps
from django.conf import settings

def get_user_model():
    return apps.get_model(settings.AUTH_USER_MODEL)

def get_channel_model():
    return apps.get_model('chat', 'Channel')

def get_chat_message_model():
    return apps.get_model('chat', 'ChatMessage')