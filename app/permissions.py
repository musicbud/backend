from rest_framework.permissions import BasePermission
from asgiref.sync import sync_to_async

class AsyncIsAuthenticated(BasePermission):
    async def has_permission(self, request, view):
        return bool(request.user and await sync_to_async(lambda: request.user.is_authenticated)())
