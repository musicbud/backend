from neomodel import AsyncStructuredNode, StringProperty, IntegerProperty, UniqueIdProperty

class SpotifyImage(AsyncStructuredNode):
    uid = UniqueIdProperty()
    url = StringProperty(unique_index=True, required=True)
    height = IntegerProperty()
    width = IntegerProperty()

    async def serialize(self):
        return {
            'uid': self.uid,
            'url': self.url,
            'height': self.height,
            'width': self.width,
            }