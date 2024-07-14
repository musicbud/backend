
import time
from neomodel import ( StringProperty,RelationshipTo,ZeroOrMore)

from ..User import User
from ..Artist import Artist
from ..Track import Track
from ..Genre import Genre
from ..Album import Album
from ..Library_Item_Rel import LibraryItemRel

class YtmusicUser(User):
    channel_handle = StringProperty()
    account_name = StringProperty()

    library_artists = RelationshipTo(Artist, 'LIBRARY_ARTIST', model=LibraryItemRel)
    library_tracks = RelationshipTo(Track, 'LIBRARY_TRACK', model=LibraryItemRel)
    library_albums = RelationshipTo(Album, 'LIBRARY_ALBUM', model=LibraryItemRel)

    likes_track = RelationshipTo(Track, 'LIKES_TRACK', cardinality=ZeroOrMore)
    
    

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