
from neomodel import StringProperty,IntegerProperty,RelationshipFrom,RelationshipTo,ZeroOrMore,UniqueIdProperty
from ..Genre import Genre

class SpotifyGenre(Genre):
    
    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }