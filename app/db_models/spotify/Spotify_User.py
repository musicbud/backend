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

    likes_artist = RelationshipTo(Artist, 'LIKES_ARTIST', cardinality=ZeroOrMore)
    likes_track = RelationshipTo(Track, 'LIKES_TRACK', cardinality=ZeroOrMore)
    likes_genre = RelationshipTo(Genre, 'LIKES_GENRE', cardinality=ZeroOrMore)
    likes_album = RelationshipTo(Album, 'LIKES_ALBUM', cardinality=ZeroOrMore)
    
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


