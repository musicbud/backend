from neomodel import AsyncStructuredNode, StringProperty

class MainPicture(AsyncStructuredNode):
    medium = StringProperty()
    large = StringProperty()