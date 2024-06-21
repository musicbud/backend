from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from django.utils.translation import gettext_lazy as _
import time
from myapp.models import User 

class CustomTokenAuthentication(TokenAuthentication):

    def authenticate(self, request):
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            auth = auth.split('Bearer ')[1]
        if not auth:
            return None
        return self.authenticate_credentials(auth)
    
    def authenticate_credentials(self, token):
        token_string = token.decode('utf-8') if isinstance(token, bytes) else token

        try:
            user = User.nodes.get(access_token=token_string)
        except User.DoesNotExist as e:
            print(token_string)
            raise AuthenticationFailed(_('Invalid token.'))

        if not user.is_active:
            raise AuthenticationFailed(_('User inactive or deleted.'))

        # if self.is_token_expired(user):
            # raise AuthenticationFailed(_('Access token expired.'))
        user.is_authenticated = True

        return (user, token_string)

    def is_token_expired(self, user):
        current_time = time.time()
        issue_time = user.token_issue_time  # Assuming you have a field to store the token issue time
        expires_at = user.expires_at  # Assuming you have a field to store the expiration duration

        # Calculate the expiration time by adding the issue time and expiration duration
        expiration_time = issue_time + expires_at

        return current_time >= expiration_time
    