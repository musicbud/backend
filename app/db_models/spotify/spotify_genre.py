from neomodel import StringProperty
from ..genre import Genre

class SpotifyGenre(Genre):
    element_id_property = StringProperty()

    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'element_id_property': self.element_id_property,
        }