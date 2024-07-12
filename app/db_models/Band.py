
from neomodel import  StringProperty,RelationshipFrom,UniqueIdProperty
from .Artist import Artist
from .Liked_Item import LikedItem
class Band(LikedItem):
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True, required=True)
    members = RelationshipFrom(Artist, 'MEMBER_OF')