from neomodel import StructuredNode, UniqueIdProperty,StringProperty


class LikedItem(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty( min_length=1, max_length=255)

