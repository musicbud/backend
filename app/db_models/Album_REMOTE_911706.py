from .Liked_Item import LikedItem


from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)



class Album(LikedItem):
    name = StringProperty(required=True)

    users = AsyncRelationshipFrom('.User.User', 'LIKES_ALBUM')
    tracks = AsyncRelationshipFrom('.Track.Track', 'INCLUDED_IN')
    artists = AsyncRelationshipFrom('.Artist.Artist', 'CONTRIBUTED_TO')
   