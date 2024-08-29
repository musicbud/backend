from django.urls import path
from . import views

urlpatterns = [
    path('channel/<str:channel_name>/', views.channel_chat, name='channel_chat'),
    path('users/', views.user_list, name='user_list'),
    path('chat/<str:username>/', views.user_chat, name='user_chat'),
    path('', views.chat_home, name='chat_home'),
    path('channels/', views.channel_list, name='channel_list'),
    path('create_channel/', views.create_channel, name='create_channel'),
    path('send_message/', views.send_message, name='send_message'),
    path('add_channel_member/<int:channel_id>/', views.add_channel_member, name='add_channel_member'),
    # Add these new paths for channel management
    path('channel/<int:channel_id>/dashboard/', views.channel_dashboard, name='channel_dashboard'),
    path('channel/<int:channel_id>/accept_user/<int:user_id>/', views.accept_user, name='accept_user'),
    path('channel/<int:channel_id>/kick_user/<int:user_id>/', views.kick_user, name='kick_user'),
    path('channel/<int:channel_id>/block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('handle_invitation/<int:invitation_id>/<str:action>/', views.handle_invitation, name='handle_invitation'),
    path('channel/<int:channel_id>/add_moderator/<int:user_id>/', views.add_moderator, name='add_moderator'),
    path('chat/channel/<str:room_name>/', views.chat_room, name='chat_room'),
]