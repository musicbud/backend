from django.urls import path
from chat import views

urlpatterns = [
    path('channel/<int:channel_id>/', views.channel_dashboard, name='channel_dashboard'),
    path('channel/<int:channel_id>/accept_user/<int:user_id>/', views.accept_user, name='accept_user'),
    path('channel/<int:channel_id>/kick_user/<int:user_id>/', views.kick_user, name='kick_user'),
    path('channel/<int:channel_id>/block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('handle_invitation/<int:invitation_id>/<str:action>/', views.handle_invitation, name='handle_invitation'),
    path('channel/<int:channel_id>/add_moderator/<int:user_id>/', views.add_moderator, name='add_moderator'),
    path('create_channel/', views.create_channel, name='create_channel'),
]
