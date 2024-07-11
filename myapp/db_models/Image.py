from neomodel import StructuredNode, StringProperty,DateTimeProperty,IntegerProperty,RelationshipTo
from .Image_Sizes import ImageSizes

# Image node with a relationship to ImageSizes
class Image(StructuredNode):
    title = StringProperty()
    url = StringProperty()
    dateadded = DateTimeProperty()
    format = StringProperty()
    owner = StringProperty()
    votes = IntegerProperty()
    sizes = RelationshipTo(ImageSizes, 'HAS_SIZE')
