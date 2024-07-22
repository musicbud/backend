
from neomodel import StringProperty,IntegerProperty,RelationshipFrom,RelationshipTo,ZeroOrMore,UniqueIdProperty
from .Liked_Item import LikedItem
from .Artist import Artist

class Genre(LikedItem):

    artists = RelationshipTo(Artist, 'HAS_ARTIST')
    users = RelationshipFrom('.User.User', 'LIKES')


    