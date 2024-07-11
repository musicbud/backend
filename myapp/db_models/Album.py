from neomodel import StructuredNode, StringProperty,RelationshipFrom

class Album(StructuredNode):
    uid = StringProperty()
    name = StringProperty(required=True)
    href = StringProperty()
    artist = RelationshipFrom('Artist', 'HAS_ALBUM')
    tracks = RelationshipFrom('Track', 'IN_ALBUM')