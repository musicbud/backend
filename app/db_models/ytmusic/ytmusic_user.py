import time
from ..user import User
from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,AsyncRelationshipFrom,
    UniqueIdProperty, AsyncRelationshipTo)

class YtmusicUser( User):
    channel_handle = StringProperty()
    account_name = StringProperty()

    likes_tracks = AsyncRelationshipTo('..track.Track', 'LIKES_TRACK')    
    likes_artists = AsyncRelationshipTo('..artist.Artist', 'LIKES_ARTIST')
    played_tracks = AsyncRelationshipTo('..track.Track', 'PLAYED_TRACK')

    parent = AsyncRelationshipFrom('..user.User', 'CONNECTED_TO_YTMUSIC')



    @classmethod
    async def update_ytmusic_tokens(cls, user, tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_issue_time = time.time()
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.scope = tokens['scope']
        user.is_active = True
        user.service = 'ytmusic'

        await user.save()
        return user

    @classmethod
    async def create_from_ytmusic_profile(cls, profile, tokens):
        user_data = {
            'account_name': profile['accountName'],
            'channel_handle': profile['channelHandle'],
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_at': tokens['expires_at'],
            'token_issue_time': time.time(),
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'scope': tokens['scope'],
            'service': 'ytmusic'
        }
        user = cls(**user_data)
        await user.save()
        return user
    
    async def get_likes(self):
        return {
            'likes_tracks': [track for track in await self.likes_tracks.all()],
            'played_tracks': [track for track in await self.played_tracks.all()],
            'likes_artists': [artist for artist in await self.likes_artists.all()],
        }

    async def serialize(self):
        likes_tracks = await self.likes_tracks.all()
        played_tracks = await self.played_tracks.all()
        likes_artists = await self.likes_artists.all()

        return {
            'uid': self.uid,
            'account_name': self.account_name,
            'channel_handle': self.channel_handle,
            'likes_tracks': [await track.serialize() for track in likes_tracks],
            'played_tracks': [await track.serialize() for track in played_tracks],
            'likes_artists': [ await artist.serialize() for artist in likes_artists],
        }