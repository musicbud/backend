import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import authenticate, login
from asgiref.sync import sync_to_async
from app.db_models.parent_user import ParentUser

class LoginConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        username = text_data_json['username']
        password = text_data_json['password']

        user = await sync_to_async(authenticate)(self.scope, username=username, password=password)

        if user is not None:
            await sync_to_async(login)(self.scope, user)
            await self.send(text_data=json.dumps({
                'message': 'Login successful'
            }))
        else:
            await self.send(text_data=json.dumps({
                'error': 'Invalid credentials'
            }))

class GetProfileConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        user = self.scope["user"]
        user_data = await sync_to_async(self.get_user_data)(user)
        await self.send(text_data=json.dumps(user_data))

    def get_user_data(self, user):
        return {
            'username': user.username,
            'email': user.email,
            # Add other fields as needed
        }
