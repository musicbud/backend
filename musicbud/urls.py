from django.contrib import admin
from django.urls import path, include
from app.views import auth_views  # Import auth_views instead of views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('app.urls')),
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
]
