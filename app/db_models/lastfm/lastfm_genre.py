from neomodel import StructuredNode, StringProperty
from ..genre import Genre

class LastfmGenre(StructuredNode):
    __label__ = 'LastfmGenre'
    name = StringProperty(unique_index=True)
    
    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            }