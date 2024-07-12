
from neomodel import StringProperty,IntegerProperty,RelationshipFrom,RelationshipTo,ZeroOrMore
from .Liked_Item import LikedItem
from .Artist import Artist
class Genre(LikedItem):
    uid = StringProperty( unique_index=True)
    href = StringProperty( min_length=1, max_length=255)
    name = StringProperty( min_length=1, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( min_length=1, max_length=255)
    uri = StringProperty( min_length=1, max_length=255)
    liked_by = RelationshipFrom('User', 'LIKES_GENRE',cardinality=ZeroOrMore)
    artists = RelationshipTo(Artist, 'HAS_ARTIST')

    def serialize(self):
        return {
            'uid': self.uid,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri,
            'artists':self.artists
        }