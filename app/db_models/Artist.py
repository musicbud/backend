from .Liked_Item import LikedItem

from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)


class Artist(LikedItem):
    name = StringProperty( max_length=255)
    
    top_items = AsyncRelationshipFrom('.User', 'TOP_ARTIST')
    library_items = AsyncRelationshipFrom('.User', 'LIBRARY_ITEM')

    users = AsyncRelationshipFrom('.User.User', 'LIKES_ARTIST')
    tracks = AsyncRelationshipFrom('.Track.Track', 'PERFORMED_BY')
    albums = AsyncRelationshipFrom('.Album.Album', 'CONTRIBUTED_TO')

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            }
    