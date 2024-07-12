
from neomodel import StructuredNode, StringProperty,RelationshipFrom
from .Artist import Artist
class Band(StructuredNode):
    uid = StringProperty()
    name = StringProperty(unique_index=True, required=True)
    members = RelationshipFrom(Artist, 'MEMBER_OF')