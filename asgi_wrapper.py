import asyncio
from django.http import HttpResponse, JsonResponse
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ASGIWrapper:
    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            return await self.handle_http(scope, receive, send)
        return await self.application(scope, receive, send)

    async def handle_http(self, scope, receive, send):
        async def wrapped_send(event):
            if event['type'] == 'http.response.start':
                headers = event.get('headers', [])
                headers.append((b'Content-Type', b'application/json'))
                event['headers'] = headers
            await send(event)

        try:
            instance = self.application(scope)
            response = await instance(receive, wrapped_send)
            if asyncio.iscoroutine(response):
                response = await response
            if not isinstance(response, (HttpResponse, JsonResponse)):
                response = HttpResponse(str(response))
            await self.send_response(wrapped_send, response)
        except Exception as e:
            logger.error(f"ASGIWrapper: Error in handle_http: {str(e)}")
            response = JsonResponse({"error": str(e)}, status=500)
            await self.send_response(wrapped_send, response)

    async def send_response(self, send, response):
        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': [
                (key.encode('utf-8'), value.encode('utf-8'))
                for key, value in response.items()
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': response.content,
        })
