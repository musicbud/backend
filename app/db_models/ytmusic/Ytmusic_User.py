
import time
from neomodel import ( StringProperty)
from ..User import User

class YtmusicUser(User):
    channel_handle = StringProperty()
    account_name = StringProperty()

    @classmethod
    def update_ytmusic_tokens(cls, user, tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_issue_time = time.time()
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.scope = tokens['scope']
        user.is_active = True
        user.save()
        return user

    @classmethod
    def create_from_ytmusic_profile(cls, profile, tokens):
        user_data = {
            'account_name': profile['accountName'],
            'channel_handle': profile['channelHandle'],
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_at': tokens['expires_at'],
            'token_issue_time': time.time(),
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'scope': tokens['scope']
        }
        user = cls(**user_data)
        user.save()
        return user