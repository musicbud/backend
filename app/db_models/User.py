from neomodel import (StructuredNode, IntegerProperty, db, BooleanProperty, ZeroOrMore,
                      StringProperty, RelationshipTo, ArrayProperty, UniqueIdProperty)
from .Artist import Artist
from .Track import Track
from .Genre import Genre
from .Album import Album
from .Top_Item_Rel import TopItemRel


class User(StructuredNode):
    uid = UniqueIdProperty()
   
    email = StringProperty(unique_index=True, email=True, min_length=1, max_length=255)
    country = StringProperty()
    display_name = StringProperty(min_length=1, max_length=255)
    bio = StringProperty()
    is_active = BooleanProperty()
    is_authenticated = BooleanProperty()
    service = StringProperty()

    access_token = StringProperty()
    refresh_token = StringProperty()
    expires_at = IntegerProperty()
    expires_in = IntegerProperty()
    token_issue_time = StringProperty()
    token_type = StringProperty()
    scope = ArrayProperty()

    @classmethod
    def set_and_update_bio(cls, user_id, bio):
        user = cls.nodes.get_or_none(uid=user_id)
        if user:
            user.bio = bio
            user.save()
            return True
        return False
    
    

