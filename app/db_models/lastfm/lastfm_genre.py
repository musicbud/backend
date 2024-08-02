
from neomodel import StringProperty
from ..genre import Genre

class LastfmGenre(Genre):
    name = StringProperty( min_length=1, max_length=255)
    
    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            }