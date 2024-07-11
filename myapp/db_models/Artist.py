from neomodel import StringProperty,IntegerProperty,RelationshipFrom,ZeroOrMore

from Liked_Item import LikedItem
from .Top_Item_Rel import TopItemRel
from .Library_Item_Rel import LibraryItemRel
from .Similar_Item_Rel import SimilarItemRel


class Artist(LikedItem):
    uid = StringProperty( unique_index=True)
    browse_id = StringProperty(unique_index=True)
    href = StringProperty( unique_index=True, max_length=255)
    name = StringProperty( max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( max_length=255)
    uri = StringProperty( max_length=255)
    top_items = RelationshipFrom('User', 'TOP_ARTIST', model=TopItemRel)
    similar_items = RelationshipFrom('Artist', 'SIMILAR_ARTIST', model=SimilarItemRel)
    library_items = RelationshipFrom('User', 'LIBRARY_ITEM', model=LibraryItemRel)

    liked_by = RelationshipFrom('User', 'LIKES_ARTIST',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'browse_id':self.browse_id,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri,
            'top_items' : self.top_items,
            'similar_items' : self.similar_items,
            'library_items': self.library_items
        }
