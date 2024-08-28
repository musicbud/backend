from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import DjangoParentUser

admin.site.register(DjangoParentUser, UserAdmin)
