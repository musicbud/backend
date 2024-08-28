import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Channel, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        message_type = data['type']

        if message_type == 'channel':
            await self.save_channel_message(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.scope['user'].username
                }
            )
        elif message_type == 'user':
            recipient_username = data['recipient']
            await self.save_user_message(message, recipient_username)
            await self.send_user_message(message, recipient_username)

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    @database_sync_to_async
    def save_channel_message(self, message):
        user = self.scope['user']
        channel = Channel.objects.get(name=self.room_name)
        Message.objects.create(sender=user, content=message, channel=channel)

    @database_sync_to_async
    def save_user_message(self, message, recipient_username):
        user = self.scope['user']
        recipient = User.objects.get(username=recipient_username)
        Message.objects.create(sender=user, content=message, recipient=recipient)

    async def send_user_message(self, message, recipient_username):
        await self.channel_layer.group_send(
            f'user_{recipient_username}',
            {
                'type': 'user_message',
                'message': message,
                'sender': self.scope['user'].username
            }
        )

    async def user_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'type': 'user'
        }))
