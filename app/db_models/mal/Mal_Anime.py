from neomodel import UniqueIdProperty,AsyncStructuredNode, StringProperty, IntegerProperty, BooleanProperty, JSONProperty, DateTimeProperty

class Anime(AsyncStructuredNode):
    uid = UniqueIdProperty()
    anime_id = IntegerProperty(unique_index=True)
    title = StringProperty(required=True)
    main_picture = JSONProperty(default={})
    status = StringProperty(required=True)
    score = IntegerProperty(default=0)
    num_watched_episodes = IntegerProperty(default=0)
    is_rewatching = BooleanProperty(default=False)
    updated_at = DateTimeProperty()