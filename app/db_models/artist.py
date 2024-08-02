from .liked_item import LikedItem

from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo, AsyncRelationshipFrom)


class Artist(LikedItem):
    name = StringProperty( max_length=255)
    
    top_items = AsyncRelationshipFrom('.user', 'TOP_ARTIST')
    library_items = AsyncRelationshipFrom('.user', 'LIBRARY_ITEM')

    users = AsyncRelationshipFrom('.user.User', 'LIKES_ARTIST')
    tracks = AsyncRelationshipFrom('.track.Track', 'PERFORMED_BY')
    albums = AsyncRelationshipFrom('.album.Album', 'CONTRIBUTED_TO')

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            }
    