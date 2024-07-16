
from neomodel import StringProperty,IntegerProperty,RelationshipFrom,RelationshipTo,ZeroOrMore,UniqueIdProperty
from .Liked_Item import LikedItem
from .Artist import Artist

class Genre(LikedItem):
    uid = UniqueIdProperty()
    name = StringProperty( min_length=1, max_length=255)

    artists = RelationshipTo(Artist, 'HAS_ARTIST')
    users = RelationshipFrom('.User.User', 'LIKES')


    