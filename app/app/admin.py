from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import DjangoParentUser

class CustomUserAdmin(UserAdmin):
    model = DjangoParentUser
    list_display = ['username', 'email', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ()}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ()}),
    )

admin.site.register(DjangoParentUser, CustomUserAdmin)
