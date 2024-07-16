from neomodel import StringProperty,RelationshipFrom,RelationshipTo

from .Liked_Item import LikedItem
from .Top_Item_Rel import TopItemRel
from .Library_Item_Rel import LibraryItemRel


class Artist(LikedItem):
    name = StringProperty( max_length=255)
    
    top_items = RelationshipFrom('.User.User', 'TOP_ARTIST', model=TopItemRel)
    library_items = RelationshipFrom('.User.User', 'LIBRARY_ITEM', model=LibraryItemRel)

    users = RelationshipFrom('.User.User', 'LIKES_ARTIST')
    tracks = RelationshipTo('.Track.Track', 'PERFORMED_BY')
    albums = RelationshipTo('.Album.Album', 'CONTRIBUTED_TO')

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            }
    