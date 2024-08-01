from .liked_item import LikedItem


from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)



class Album(LikedItem):
    name = StringProperty(required=True)

    users = AsyncRelationshipFrom('.user.User', 'LIKES_ALBUM')
    tracks = AsyncRelationshipFrom('.track.Track', 'INCLUDED_IN')
    artists = AsyncRelationshipFrom('.artist.Artist', 'CONTRIBUTED_TO')
   