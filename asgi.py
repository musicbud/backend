import os
from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler
from django.core.handlers.base import BaseHandler
from django.core.handlers.exception import convert_exception_to_response
from django.utils.decorators import sync_and_async_middleware
from your_app.middlewares.jwt_auth_middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

application = get_asgi_application()

@sync_and_async_middleware
def jwt_middleware(get_response):
    return JWTAuthMiddleware(get_response)

class CustomASGIHandler(ASGIHandler):
    def __init__(self):
        super().__init__()
        self.load_middleware(is_async=True)
        self._middleware_chain = self.get_response_async
        self._middleware_chain = jwt_middleware(self._middleware_chain)

    async def get_response_async(self, request):
        response = await super().get_response_async(request)
        return response

application = CustomASGIHandler()
