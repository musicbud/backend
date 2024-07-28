
from .Liked_Item import LikedItem
from .Artist import Artist
from .Track import Track



from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)

class Genre(LikedItem):
    name = StringProperty()
    artists = AsyncRelationshipTo(Artist, 'HAS_ARTIST')
    users = AsyncRelationshipFrom('.User.User', 'LIKES')
    tracks = AsyncRelationshipTo(Track, 'HAS_TRACK')


    