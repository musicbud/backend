from django.contrib import admin
from django.urls import path, include
from app.views.auth_views import AuthLogin, register_view
from app.views.home_views import home
from chat.views import user_list, channel_list  # Import the view function

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
    path('login/', AuthLogin.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('', home, name='home'),
    path('', include('app.urls')),
    path('users/', user_list, name='user_list'),
    path('channels/', channel_list, name='channel_list'),
]
