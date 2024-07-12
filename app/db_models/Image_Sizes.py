from neomodel import StructuredNode, StringProperty

# ImageSizes node
class ImageSizes(StructuredNode):
    original = StringProperty()
    large = StringProperty()
    largesquare = StringProperty()
    medium = StringProperty()
    small = StringProperty()
    extralarge = StringProperty()

