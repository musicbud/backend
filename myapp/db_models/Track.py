from neomodel import IntegerProperty, StringProperty,RelationshipFrom,ZeroOrMore

from Liked_Item import LikedItem

class Track(LikedItem):
    uid = StringProperty( unique_index=True)
    video_id = StringProperty()
    href = StringProperty( min_length=1, max_length=255)
    name = StringProperty( min_length=1, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( min_length=1, max_length=255)
    uri = StringProperty( min_length=1, max_length=255)
    liked_by = RelationshipFrom('User', 'LIKES_TRACK',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'video_id':self.video_id,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri
        }
