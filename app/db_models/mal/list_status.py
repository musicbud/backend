
from neomodel import AsyncStructuredNode, StringProperty,BooleanProperty,IntegerProperty,DateTimeProperty

class ListStatus(AsyncStructuredNode):
    status = StringProperty(required=True)
    is_rereading = BooleanProperty(default=False)
    num_volumes_read = IntegerProperty(default=0)
    num_chapters_read = IntegerProperty(default=0)
    score = IntegerProperty(default=0)
    updated_at = DateTimeProperty()