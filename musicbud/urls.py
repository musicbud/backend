from django.urls import path,re_path
from rest_framework import permissions
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from musicbud import settings

urlpatterns = [
    path('msucibud/admin', admin.site.urls),
    path('musicbud/', include('myapp.urls')),
    path('musicbud/chat/', include('chat.urls')),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
