from .liked_item import LikedItem
from neomodel import (StringProperty, IntegerProperty, AsyncRelationshipTo, AsyncRelationshipFrom)


class Artist(LikedItem):
    name = StringProperty(max_length=255)
    
    top_items = AsyncRelationshipFrom('.user', 'TOP_ARTIST')
    library_items = AsyncRelationshipFrom('.user', 'LIBRARY_ITEM')

    users = AsyncRelationshipFrom('.user.User', 'LIKES_ARTIST')
    tracks = AsyncRelationshipFrom('.track.Track', 'PERFORMED_BY')
    albums = AsyncRelationshipFrom('.album.Album', 'CONTRIBUTED_TO')

    async def serialize(self):
        base_data = await super().serialize()
        artist_data = {
            'name': self.name,
        }
        return {**base_data, **artist_data}

