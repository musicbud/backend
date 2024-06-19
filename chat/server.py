import os
import sys
import django
import asyncio
import websockets
import json
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

# Django setup
sys.path.append('/home/mahmoud/Documents/GitHub/musicbud-revanced')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbud.settings')
django.setup()

# Import Django models after setup
from myapp.CustomTokenAuthentication import CustomTokenAuthentication
from myapp.chat.models import Message

User = get_user_model()
connected_clients = set()
custom_auth = CustomTokenAuthentication()

async def register(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def send_personal_message(message, recipient_username):
    for client in connected_clients:
        if hasattr(client, 'username') and client.username == recipient_username:
            await client.send(message)
            break

async def handle_message(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        token = data.get('token')
        try:
            user, _ = custom_auth.authenticate_credentials(token)
            content = data.get('message')

            # Save message to the database
            msg = Message(username=user.username, message=content)
            msg.save()

            # Send message to the intended recipient
            await send_personal_message(json.dumps({
                'username': user.username,
                'message': content,
                'timestamp': msg.timestamp.isoformat()
            }), data.get('recipient'))

        except AuthenticationFailed as e:
            await websocket.send(json.dumps({'error': str(e)}))

async def main():
    async with websockets.serve(handle_message, "localhost", 6789):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())







# import os
# import sys
# import django
# sys.path.append('/home/mahmoud/Documents/GitHub/musicbud-revanced')
# # Setup Django settings and initialize
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbud.settings')
# django.setup()

# # Now you can import Django models and other components
# from myapp.CustomTokenAuthentication import CustomTokenAuthentication
# from myapp.chat.models import Message

# import asyncio
# import websockets
# import json
# from django.contrib.auth import get_user_model
# from rest_framework.exceptions import AuthenticationFailed
# import time

# User = get_user_model()
# connected_clients = set()
# custom_auth = CustomTokenAuthentication()

# async def register(websocket):
#     connected_clients.add(websocket)
#     try:
#         await websocket.wait_closed()
#     finally:
#         connected_clients.remove(websocket)

# async def send_message(message):
#     if connected_clients:
#         await asyncio.wait([client.send(message) for client in connected_clients])

# async def handle_message(websocket, path):
#     async for message in websocket:
#         data = json.loads(message)
#         token = data.get('token')
#         try:
#             user, _ = custom_auth.authenticate_credentials(token)
#             content = data.get('message')

#             # Save message to the database
#             msg = Message(username=user.username, message=content)
#             msg.save()

#             # Broadcast message to all connected clients
#             await send_message(json.dumps({
#                 'username': user.username,
#                 'message': content,
#                 'timestamp': msg.timestamp.isoformat()
#             }))
#         except AuthenticationFailed as e:
#             await websocket.send(json.dumps({'error': str(e)}))

# async def main():
#     async with websockets.serve(handle_message, "localhost", 6789):
#         await asyncio.Future()  # run forever

# if __name__ == "__main__":
#     asyncio.run(main())


