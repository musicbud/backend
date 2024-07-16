import time
from neomodel import ( StringProperty,RelationshipTo,ZeroOrMore)

from ..User import User
from ..Artist import Artist
from ..Track import Track
from ..Genre import Genre
from ..Album import Album
from ..Top_Item_Rel import TopItemRel

class SpotifyUser(User):
    spotify_id = StringProperty(unique_index=True)
    username = StringProperty(unique_index=True)

    top_artists = RelationshipTo(Artist, 'TOP_ARTIST', model=TopItemRel)
    top_tracks = RelationshipTo(Track, 'TOP_TRACK', model=TopItemRel)
    top_genres = RelationshipTo(Genre, 'TOP_GENRE', model=TopItemRel)

    likes_artists = RelationshipTo(Artist, 'LIKES_ARTIST')
    likes_tracks = RelationshipTo(Track, 'LIKES_TRACK')
    likes_genres = RelationshipTo(Genre, 'LIKES_GENRE')
    likes_albums = RelationshipTo(Album, 'LIKES_ALBUM')
    
    @classmethod
    def update_spotify_tokens(cls, user, tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.token_issue_time = time.time()
        user.is_active = True
        user.service = 'spotify'
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
            'expires_at': tokens['expires_at'],
            'spotify_id':profile.get('id', None),
            'service' :'spotify'

        }
        user = cls(**user_data)
        user.save()
        return user
    
    @classmethod
    def get_profile(cls, user):
        return {
            'top_artists': [artist.serialize() for artist in user.top_artists],
            'top_tracks': [track.serialize() for track in user.top_tracks],
            'top_genres': [genre.serialize() for genre in user.top_genres],
            'likes_artists': [artist.serialize() for artist in user.likes_artists],
            'likes_tracks': [track.serialize() for track in user.likes_tracks],
            'likes_genres': [genre.serialize() for genre in user.likes_genres],
            'likes_albums': [album.serialize() for album in user.likes_albums],
        }


