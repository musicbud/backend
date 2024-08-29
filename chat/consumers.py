import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Channel, ChatMessage
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

        # Fetch and send recent messages
        await self.send_chat_history()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Save message to database
        await self.save_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.scope["user"].username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    @database_sync_to_async
    def save_message(self, message):
        user = self.scope["user"]
        channel, _ = Channel.objects.get_or_create(name=self.room_name)
        ChatMessage.objects.create(channel=channel, author=user, content=message)

    @database_sync_to_async
    def get_recent_messages(self):
        channel, _ = Channel.objects.get_or_create(name=self.room_name)
        return list(ChatMessage.objects.filter(channel=channel).select_related('author').order_by('-timestamp')[:50])

    async def send_chat_history(self):
        messages = await self.get_recent_messages()
        for message in reversed(messages):
            await self.send(text_data=json.dumps({
                'message': message.content,
                'username': message.author.username,
            }))

