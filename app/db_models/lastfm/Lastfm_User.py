import time

from neomodel import ( StringProperty,RelationshipTo,ZeroOrMore)

from ..User import User
from ..Artist import Artist
from ..Track import Track
from ..Genre import Genre
from ..Album import Album
from ..Top_Item_Rel import TopItemRel


class LastfmUser(User):
    username = StringProperty(unique_index=True)
    top_artists = RelationshipTo(Artist, 'TOP_ARTIST', model=TopItemRel)
    top_tracks = RelationshipTo(Track, 'TOP_TRACK', model=TopItemRel)
    top_genres = RelationshipTo(Genre, 'TOP_GENRE', model=TopItemRel)

    likes_artists = RelationshipTo(Artist, 'LIKES_ARTIST', cardinality=ZeroOrMore)
    likes_tracks = RelationshipTo(Track, 'LIKES_TRACK', cardinality=ZeroOrMore)
    likes_genres = RelationshipTo(Genre, 'LIKES_GENRE', cardinality=ZeroOrMore)
    likes_albums = RelationshipTo(Album, 'LIKES_ALBUM', cardinality=ZeroOrMore)
    played_tracks = RelationshipTo(Track, 'PLAYED_TRACK', cardinality=ZeroOrMore)


    @classmethod
    def update_lastfm_tokens(cls, user, token):
        user.access_token = token
        user.token_issue_time = str(time.time())
        user.is_active = True
        user.service = 'lastfm'
        user.save()
        return user

    @classmethod
    def create_from_lastfm_profile(cls, profile, token):
        user_data = {
            'username': profile['username'],
            'access_token': token,
            'service' : 'lastfm'

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
            'played_tracks': [track.serialize() for track in user.played_tracks],

        }
