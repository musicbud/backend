from neomodel import (AsyncStructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, AsyncRelationshipTo)
from neomodel import (StringProperty, IntegerProperty, BooleanProperty, ArrayProperty, UniqueIdProperty)

class User(AsyncStructuredNode):
    uid = UniqueIdProperty()
   
    email = StringProperty(unique_index=True, email=True, min_length=1, max_length=255)
    country = StringProperty()
    display_name = StringProperty(min_length=1, max_length=255)
    is_active = BooleanProperty()
    service = StringProperty()

    access_token = StringProperty()
    refresh_token = StringProperty()
    expires_at = IntegerProperty()
    expires_in = IntegerProperty()
    token_issue_time = StringProperty()
    token_type = StringProperty()
    scope = ArrayProperty()

    parent_user = AsyncRelationshipTo('.Parent_User.ParentUser', 'CONNECTED_TO_PARENT')

    @classmethod
    async def set_and_update_bio(cls, user_id, bio):
        user = await cls.nodes.get_or_none(uid=user_id)
        if user:
            user.bio = bio
            await user.save()
            return True
        return False
