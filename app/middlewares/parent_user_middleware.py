import logging
from asgiref.sync import sync_to_async
from app.db_models.parent_user import ParentUser
import asyncio
from django.utils.deprecation import MiddlewareMixin
logger = logging.getLogger(__name__)


class ParentUserMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        response = await self.process_request(request)
        if asyncio.iscoroutine(response):
            response = await response
        return response

    async def process_request(self, request):
        user = request.user
        if user and user.is_authenticated:
            parent_user = await self.get_parent_user(user.username)
            request.parent_user = parent_user
        else:
            request.parent_user = None

        response = self.get_response(request)
        if asyncio.iscoroutine(response):
            response = await response
        return response
    
    async def get_parent_user(self, username):
        from app.db_models.parent_user import ParentUser

        try:
            return await ParentUser.nodes.get(username=username)
        except ParentUser.DoesNotExist:
            return None
