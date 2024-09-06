import asyncio
from django.core.handlers.asgi import ASGIHandler
from django.http import HttpResponse, JsonResponse
import logging
from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest
import tempfile

logger = logging.getLogger(__name__)

class CustomASGIHandler(ASGIHandler):
    async def __call__(self, scope, receive, send):
        """
        Async entrypoint - parses the request and hands off to get_response.
        """
        try:
            body_file = tempfile.SpooledTemporaryFile(max_size=1024 * 1024)
            request = ASGIRequest(scope, body_file)
            response = await self.get_response_async(request)
            await self.send_response(send, response)
        except Exception as e:
            logger.error(f"Error in __call__: {str(e)}")
            await self.send_response(send, HttpResponse("Internal Server Error", status=500))
        finally:
            body_file.close()

    async def get_response_async(self, request):
        try:
            response = await super().get_response_async(request)
            if asyncio.iscoroutine(response):
                response = await response
            if not isinstance(response, (HttpResponse, JsonResponse)):
                if isinstance(response, dict):
                    response = JsonResponse(response)
                else:
                    response = HttpResponse(str(response))
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
            return response
        except Exception as e:
            logger.error(f"Error in get_response_async: {str(e)}")
            return HttpResponse("Internal Server Error", status=500)

    async def send_response(self, send, response):
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (key.encode("latin1"), value.encode("latin1"))
                for key, value in response.items()
            ],
        })
        await send({
            "type": "http.response.body",
            "body": response.content,
        })