from django.urls import path
from .templates.chat import views

urlpatterns = [
    path('users/', views.user_list, name='user_list'),
    path('chat/<str:username>/', views.chat_with_user, name='chat_with_user'),
    path('channels/', views.channel_list, name='channel_list'),
    path('channels/<int:channel_id>/', views.chat_in_channel, name='chat_in_channel'),
]
