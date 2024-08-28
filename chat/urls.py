from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('channels/', views.channel_list, name='channel_list'),
    path('users/', views.user_list, name='user_list'),
    path('channel/<int:channel_id>/', views.chat_in_channel, name='chat_in_channel'),
    path('user/<str:username>/', views.chat_with_user, name='chat_with_user'),
]