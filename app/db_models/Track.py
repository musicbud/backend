from neomodel import  StringProperty,RelationshipFrom,UniqueIdProperty,RelationshipTo

from .Liked_Item import LikedItem
from .Album import Album


class Track(LikedItem):
    name = StringProperty( min_length=1, max_length=255)
    
    album =  RelationshipTo(Album, 'INCLUDED_IN')
    artist = RelationshipTo('.Artist.Artist', 'PERFORMED_BY')
    users = RelationshipFrom('.User.User', 'LIKES_TRACK')
    