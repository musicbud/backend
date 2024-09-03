from neomodel import StructuredNode, StringProperty, IntegerProperty

class Image(StructuredNode):
    url = StringProperty(unique_index=True)
    height = IntegerProperty()
    width = IntegerProperty()
