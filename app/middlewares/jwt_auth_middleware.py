import logging
from django.utils.functional import SimpleLazyObject
from asgiref.sync import sync_to_async
import asyncio

logger = logging.getLogger(__name__)

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = self._get_user(request)
        return self.get_response(request)

    def _get_user(self, request):
        from .async_jwt_authentication import AsyncJWTAuthentication

        auth = AsyncJWTAuthentication()
        try:
            user, _ = auth.authenticate(request)
            return user
        except Exception as e:
            logger.error(f"JWTAuthMiddleware: Authentication error: {str(e)}")
            return None

