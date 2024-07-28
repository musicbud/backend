from neomodel import  StringProperty,RelationshipFrom
from .Liked_Item import LikedItem

class Album(LikedItem):
    users = RelationshipFrom('.User.User', 'LIKES_ALBUM')
    tracks = RelationshipFrom('.Track.Track', 'INCLUDED_IN')
    artists = RelationshipFrom('.Artist.Artist', 'CONTRIBUTED_TO')
   