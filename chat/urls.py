from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('channels/', views.channel_list, name='channel_list'),
    path('channel/<str:room_name>/', views.channel_chat, name='channel_chat'),
    path('chat/<str:username>/', views.user_chat, name='user_chat'),
    path('channels/', views.channel_list, name='channel_list'),
    path('chat/channel/<str:channel_name>/', views.channel_chat, name='channel_chat'),
    path('create_channel/', views.create_channel, name='create_channel'),
    path('send_message/', views.send_message, name='send_message'),
    path('add_channel_member/<int:channel_id>/', views.add_channel_member, name='add_channel_member'),
]