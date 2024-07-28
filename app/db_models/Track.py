from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)
from .Liked_Item import LikedItem
from .Album import Album
class Track(LikedItem):
    name = StringProperty( min_length=1, max_length=255)
    
    album =  AsyncRelationshipTo(Album, 'INCLUDED_IN')
    artists = AsyncRelationshipTo('.Artist.Artist', 'PERFORMED_BY')
    users = AsyncRelationshipFrom('.User.User', 'LIKES_TRACK')
    