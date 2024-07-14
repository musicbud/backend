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

    likes_artist = RelationshipTo(Artist, 'LIKES_ARTIST', cardinality=ZeroOrMore)
    likes_track = RelationshipTo(Track, 'LIKES_TRACK', cardinality=ZeroOrMore)
    likes_genre = RelationshipTo(Genre, 'LIKES_GENRE', cardinality=ZeroOrMore)
    likes_album = RelationshipTo(Album, 'LIKES_ALBUM', cardinality=ZeroOrMore)

    @classmethod
    def update_lastfm_tokens(cls, user, token):
        user.access_token = token
        user.token_issue_time = str(time.time())
        user.is_active = True
        user.save()
        return user

    @classmethod
    def create_from_lastfm_profile(cls, profile, token):
        user_data = {
            'username': profile['username'],
            'access_token': token,
        }
        user = cls(**user_data)
        user.save()
        return user
