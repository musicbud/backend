from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from app.views.auth_views import login_view, register_view
from app.views.home_views import home
from chat.views import user_list  # Add this import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='register'),
    path('', home, name='home'),
    path('', include('app.urls')),
    path('users/', user_list, name='user_list'),  # Add this line
]
