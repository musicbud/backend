from neomodel import StructuredNode, StringProperty,DateTimeProperty,IntegerProperty

# LovedTrack node
class LovedTrack(StructuredNode):
    track = StringProperty()
    date = DateTimeProperty()
    timestamp = IntegerProperty()

