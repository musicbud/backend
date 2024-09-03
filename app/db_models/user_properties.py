from neomodel import (AsyncStructuredNode, StringProperty, UniqueIdProperty, DateTimeProperty)

class UserProperties(AsyncStructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    password = StringProperty(required=True)
    date_joined = DateTimeProperty(default_now=True)

    class Meta:
        abstract = True
