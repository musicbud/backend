from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo)

class LikedItem(AsyncStructuredNode):
    uid = UniqueIdProperty()
