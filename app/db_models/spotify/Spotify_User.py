import time
from neomodel import ( StringProperty)
from ..User import User

class SpotifyUser(User):
    spotify_id = StringProperty(unique_index=True)
    username = StringProperty(unique_index=True)
    
    @classmethod
    def update_spotify_tokens(cls, user, tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.token_issue_time = time.time()
        user.is_active = True
        user.save()
        return user

    @classmethod
    def create_from_spotify_profile(cls, profile, tokens):
        user_data = {
            'uid': profile.get('uid', None),
            'country': profile.get('country', None),
            'display_name': profile.get('display_name', None),
            'email': profile.get('email', None),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'expires_at': tokens['expires_at']
        }
        user = cls(**user_data)
        user.save()
        return user


