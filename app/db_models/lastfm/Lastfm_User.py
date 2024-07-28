import time
from ..User import User
from ..Artist import Artist
from ..Track import Track
from ..Genre import Genre
from ..Album import Album



from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)



class LastfmUser(User):
    username = StringProperty(unique_index=True)
    top_artists = AsyncRelationshipTo('Artist', 'TOP_ARTIST')
    top_tracks = AsyncRelationshipTo('Track', 'TOP_TRACK')
    top_genres = AsyncRelationshipTo('Genre', 'TOP_GENRE')

    likes_artists = AsyncRelationshipTo('Artist', 'LIKES_ARTIST')
    likes_tracks = AsyncRelationshipTo('Track', 'LIKES_TRACK')
    likes_genres = AsyncRelationshipTo('Genre', 'LIKES_GENRE')
    likes_albums = AsyncRelationshipTo('Album', 'LIKES_ALBUM')
    played_tracks = AsyncRelationshipTo('Track', 'PLAYED_TRACK')
    
    parent = AsyncRelationshipFrom('..User.User', 'CONNECTED_TO_LASTFM')


    @classmethod
    async def update_lastfm_tokens(cls, user, token):
        user.access_token = token
        user.token_issue_time = time.time()
        user.is_active = True
        user.service = 'lastfm'
        await user.save()  # Ensure save() supports async
        return user

    @classmethod
    async def create_from_lastfm_profile(cls, profile, token):
        user_data = {
            'username': profile['username'],
            'access_token': token,
            'service': 'lastfm'
        }
        user = cls(**user_data)
        await user.save()  # Ensure save() supports async
        return user

    
    async def get_likes(self):
        # Ensure that serialize() is an async method if it's accessing async resources
        return {
            'top_artists': [ artist for artist in await self.top_artists],
            'top_tracks': [ track for track in await self.top_tracks],
            'top_genres': [ genre for genre in await self.top_genres],
            'likes_artists': [ artist for artist in await self.likes_artists],
            'likes_tracks': [ track for track in await self.likes_tracks],
            'likes_genres': [ genre for genre in await self.likes_genres],
            'likes_albums': [ album for album in await self.likes_albums],
            'played_tracks': [ track for track in await self.played_tracks],
        }
    async def serialize(self):
        top_artists = await self.top_artists.all()
        top_tracks = await self.top_tracks.all()
        top_genres = await self.top_genres.all()
        likes_artists = await self.likes_artists.all()
        likes_tracks = await self.likes_tracks.all()
        likes_genres = await self.likes_genres.all()
        likes_albums = await self.likes_albums.all()
        played_tracks = await self.played_tracks.all()

        return {
            'uid': self.uid,
            'username': self.username,
            'top_artists': [artist.serialize() for artist in top_artists],
            'top_tracks': [track.serialize() for track in top_tracks],
            'top_genres': [genre.serialize() for genre in top_genres],
            'likes_artists': [artist.serialize() for artist in likes_artists],
            'likes_tracks': [track.serialize() for track in likes_tracks],
            'likes_genres': [genre.serialize() for genre in likes_genres],
            'likes_albums': [album.serialize() for album in likes_albums],
            'played_tracks': [track.serialize() for track in played_tracks],
        }
