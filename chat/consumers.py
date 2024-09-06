import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import Message
import re

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{slugify(self.room_name)}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name} for room: {self.room_name}")

        # Send last 50 messages to the newly connected client
        await self.send_message_history()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")

    @database_sync_to_async
    def get_message_history(self):
        messages = Message.objects.filter(room=self.room_name).order_by('-timestamp')[:50]
        return [
            {
                'message': message.content,
                'username': message.user.username if message.user else 'Anonymous',
                'timestamp': message.timestamp.isoformat(),
            }
            for message in messages
        ]

    async def send_message_history(self):
        messages = await self.get_message_history()
        for message in reversed(messages):
            await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def save_message(self, username, message):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        
        try:
            message = Message.objects.create(user=user, content=message, room=self.room_name)
            logger.info(f"Message saved: {message.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return False

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            username = text_data_json.get('username', 'Anonymous')

            # Save the message
            saved = await self.save_message(username, message)

            if saved:
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username
                    }
                )
            else:
                # Send error message back to the client
                await self.send(text_data=json.dumps({
                    'error': 'Failed to save message'
                }))
        except Exception as e:
            logger.error(f"Error in receive method: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'An error occurred while processing your message'
            }))

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

class UserChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_username = self.scope['url_route']['kwargs']['user_username']
        self.other_username = self.scope['url_route']['kwargs']['other_username']
        self.room_name = f"user_chat_{self.user_username}_{self.other_username}"
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = self.scope["user"].username

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

