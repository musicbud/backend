
from .liked_item import LikedItem
from .artist import Artist
from .track import Track



from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)

class Genre(LikedItem):
    name = StringProperty()
    artists = AsyncRelationshipTo(Artist, 'HAS_ARTIST')
    users = AsyncRelationshipFrom('.user.User', 'LIKES')
    tracks = AsyncRelationshipTo(Track, 'HAS_TRACK')


    