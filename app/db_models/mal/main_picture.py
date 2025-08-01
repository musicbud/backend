from neomodel import AsyncStructuredNode, StringProperty

class MainPicture(AsyncStructuredNode):
    medium = StringProperty()
    large = StringProperty()


    async def serialize(self):
        return {
            'medium': self.medium,
            'large': self.large,
        }
    