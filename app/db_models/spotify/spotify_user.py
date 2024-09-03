import time
from ..user import User
from ..artist import Artist
from ..track import Track
from ..genre import Genre
from ..album import Album
import logging

logger = logging.getLogger('app')  # Make sure to configure logging in your Django settings

from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)



class SpotifyUser(User):
    spotify_id = StringProperty(unique_index=True)
    username = StringProperty(unique_index=True)

    top_artists = AsyncRelationshipTo(Artist, 'TOP_ARTIST')
    top_tracks = AsyncRelationshipTo('..track.Track', 'TOP_TRACK')
    top_genres = AsyncRelationshipTo('..genre.Genre', 'TOP_GENRE')

    likes_artists = AsyncRelationshipTo(Artist, 'LIKES_ARTIST')
    likes_tracks = AsyncRelationshipTo('..track.Track', 'LIKES_TRACK')
    likes_genres = AsyncRelationshipTo('..genre.Genre', 'LIKES_GENRE')
    likes_albums = AsyncRelationshipTo('..album.Album', 'LIKES_ALBUM')
    played_tracks = AsyncRelationshipTo('..track.Track', 'PLAYED_TRACK')
    saved_tracks = AsyncRelationshipTo('..track.Track', 'SAVED_TRACK')
    saved_albums = AsyncRelationshipTo('..album.Album', 'SAVED_ALBUM')


    parent = AsyncRelationshipFrom('..parent_user.ParentUser', 'CONNECTED_TO_SPOTIFY')
    

    @classmethod
    async def update_spotify_tokens(cls, user, tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.token_issue_time = time.time()
        user.is_active = True
        user.service = 'spotify'
        await user.save()
        return user

    @classmethod
    async def create_from_spotify_profile(cls, profile, tokens):
        user_data = {
            'uid': profile.get('uid', None),
            'country': profile.get('country', None),
            'display_name': profile.get('display_name', None),
            'email': profile.get('email', None),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'expires_at': tokens['expires_at'],
            'spotify_id': profile.get('id', None),
            'service': 'spotify'
        }
        user = cls(**user_data)
        await user.save()
        return user

    
    async def get_likes(self):
        # Ensure relationships are fetched asynchronously
        top_artists = await self.top_artists.all()
        top_tracks = await self.top_tracks.all()
        top_genres = await self.top_genres.all()
        likes_artists = await self.likes_artists.all()
        likes_tracks = await self.likes_tracks.all()
        likes_genres = await self.likes_genres.all()
        likes_albums = await self.likes_albums.all()
        saved_tracks = await self.saved_tracks.all()
        saved_albums = await self.saved_albums.all()
        
        return {
            'top_artists': top_artists,
            'top_tracks': top_tracks,
            'top_genres': top_genres,
            'likes_artists': likes_artists,
            'likes_tracks': likes_tracks,
            'likes_genres':  likes_genres,
            'likes_albums':  likes_albums,
            'saved_tracks':  saved_tracks,
            'saved_albums':  saved_albums,

        }
    
    
    
    async def serialize(self):
        try:
            top_artists = await self.top_artists.all()
            top_tracks = await self.top_tracks.all()
            top_genres = await self.top_genres.all()
            likes_artists = await self.likes_artists.all()
            likes_tracks = await self.likes_tracks.all()
            likes_genres = await self.likes_genres.all()
            likes_albums = await self.likes_albums.all()
            saved_albums = await self.saved_albums.all()
            played_tracks = await self.played_tracks.all()

            logger.debug(f"Serialized data for user {self.username}:")
            logger.debug(f"Top artists: {len(top_artists)}")
            logger.debug(f"Top tracks: {len(top_tracks)}")
            logger.debug(f"Top genres: {len(top_genres)}")
            logger.debug(f"Likes artists: {len(likes_artists)}")
            logger.debug(f"Likes tracks: {len(likes_tracks)}")
            logger.debug(f"Likes genres: {len(likes_genres)}")
            logger.debug(f"Likes albums: {len(likes_albums)}")
            logger.debug(f"Saved albums: {len(saved_albums)}")
            logger.debug(f"Played tracks: {len(played_tracks)}")

            return {
                'uid': self.uid,
                'spotify_id': self.spotify_id,
                'username': self.username,
                'top_artists': [await artist.serialize() for artist in top_artists],
                'top_tracks': [await track.serialize() for track in top_tracks],
                'top_genres': [await genre.serialize() for genre in top_genres],
                'likes_artists': [await artist.serialize() for artist in likes_artists],
                'likes_tracks': [await track.serialize() for track in likes_tracks],
                'likes_genres': [await genre.serialize() for genre in likes_genres],
                'likes_albums': [await album.serialize() for album in likes_albums],
                'saved_albums': [await album.serialize() for album in saved_albums],
                'played_tracks': [await track.serialize() for track in played_tracks],
            }
        except Exception as e:
            logger.error(f"Error serializing object: {e}")
            logger.error(traceback.format_exc())
            return {}
