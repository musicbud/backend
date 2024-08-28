import os
import sys
import django
import asyncio
import websockets
import json
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Django setup
sys.path.append('/home/mahmoud/Documents/GitHub/musicbud-revanced')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbud.settings')
django.setup()

# Import Django models after setup
from chat.models import Message

User = get_user_model()
connected_clients = {}

async def handle_message(websocket, path):
    try:
        # Authenticate the user
        auth_data = await websocket.recv()
        auth_data = json.loads(auth_data)
        user = authenticate(username=auth_data['username'], password=auth_data['password'])
        
        if user is None:
            await websocket.send(json.dumps({'error': 'Authentication failed'}))
            return

        # Add the authenticated user to connected clients
        connected_clients[user.username] = websocket

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            # Save message to the database
            msg = Message.objects.create(sender=user, content=data['message'], recipient_id=data['recipient'])
            
            # Send message to the recipient if they're connected
            if data['recipient'] in connected_clients:
                await connected_clients[data['recipient']].send(json.dumps({
                    'sender': user.username,
                    'message': data['message'],
                    'timestamp': msg.timestamp.isoformat()
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if user.username in connected_clients:
            del connected_clients[user.username]

async def main():
    async with websockets.serve(handle_message, "localhost", 6789):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())






