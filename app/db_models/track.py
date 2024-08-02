from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)
from .liked_item import LikedItem
from .album import Album
class Track(LikedItem):
    name = StringProperty( min_length=1, max_length=255)
    
    album =  AsyncRelationshipTo(Album, 'INCLUDED_IN')
    artists = AsyncRelationshipTo('.artist.Artist', 'PERFORMED_BY')
    users = AsyncRelationshipFrom('.user.User', 'LIKES_TRACK')
    