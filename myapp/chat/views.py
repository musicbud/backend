from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from myapp.CustomTokenAuthentication import CustomTokenAuthentication
from myapp.models import User  # Import your User model from neomodel
from .models import Message
class MyCustomView(APIView):
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        # Authenticate user using CustomTokenAuthentication
        user = request.user
        # Example logic
        if user:
            # User authenticated, proceed with view logic
            return Response({'message': f'Hello, {user.display_name}!'})
        else:
            # Authentication failed
            return Response({'error': 'Authentication failed.'}, status=401)

class MessageListView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        messages = Message.objects.order_by('-timestamp')[:50]
        return Response([{
            'username': msg.username,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages])
