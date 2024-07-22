from neomodel import  RelationshipFrom,RelationshipTo

from .Liked_Item import LikedItem
from .Album import Album


class Track(LikedItem):    
    album =  RelationshipTo(Album, 'INCLUDED_IN')
    artist = RelationshipTo('.Artist.Artist', 'PERFORMED_BY')
    users = RelationshipFrom('.User.User', 'LIKES_TRACK')
    