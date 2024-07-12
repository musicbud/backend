
from neomodel import StringProperty,IntegerProperty,RelationshipFrom,RelationshipTo,ZeroOrMore,UniqueIdProperty
from ..Genre import Genre

class SpotifyGenre(Genre):
    uid = UniqueIdProperty()
    href = StringProperty( min_length=1, max_length=255)
    name = StringProperty( min_length=1, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( min_length=1, max_length=255)
    uri = StringProperty( min_length=1, max_length=255)
    