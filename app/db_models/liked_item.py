from neomodel import (AsyncStructuredNode, UniqueIdProperty,
    AsyncRelationshipTo)

class LikedItem(AsyncStructuredNode):
    uid = UniqueIdProperty()

    async def serialize(self):
        return {
            'uid': self.uid,
        }
