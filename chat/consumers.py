import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, Channel
from django.db import IntegrityError

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_type = self.scope['url_route']['kwargs']['room_type']
        
        if self.room_type == 'user':
            self.other_username = self.room_name.replace(f"{self.user.username}_", "").replace(f"_{self.user.username}", "")
            self.room_group_name = f'chat_{self.get_room_name(self.user.username, self.other_username)}'
        else:
            self.room_group_name = f'chat_channel_{self.room_name}'

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

        # Save the message
        saved_message = await self.save_message(self.user.username, message)

        if saved_message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username,
                    'timestamp': saved_message.timestamp.isoformat(),
                }
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'timestamp': timestamp,
        }))

    @database_sync_to_async
    def save_message(self, username, message):
        try:
            sender = User.objects.get(username=username)
            if self.room_type == 'channel':
                channel, _ = Channel.objects.get_or_create(name=self.room_name)
                return Message.objects.create(sender=sender, content=message, channel=channel)
            else:  # user-to-user chat
                recipient, created = User.objects.get_or_create(username=self.other_username)
                if created:
                    recipient.set_unusable_password()
                    recipient.save()
                return Message.objects.create(sender=sender, content=message, recipient=recipient)
        except IntegrityError as e:
            print(f"IntegrityError saving message: {str(e)}")
            return None
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @staticmethod
    def get_room_name(username1, username2):
        return '_'.join(sorted([username1, username2]))
