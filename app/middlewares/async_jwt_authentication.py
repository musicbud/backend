import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

class AsyncJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        logger.debug("Entering AsyncJWTAuthentication.authenticate")
        token = self.get_token_from_request(request)
        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = self.get_user_sync(payload)
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

    def get_token_from_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split()[1]
        return None

    def get_user_sync(self, payload):
        User = get_user_model()
        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationFailed('Token contained no recognizable user identification')

        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')