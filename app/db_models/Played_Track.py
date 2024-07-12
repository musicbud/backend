from neomodel import StructuredNode, StringProperty,DateTimeProperty,IntegerProperty

# PlayedTrack node
class PlayedTrack(StructuredNode):
    track = StringProperty()
    album = StringProperty()
    playback_date = DateTimeProperty()
    timestamp = IntegerProperty()