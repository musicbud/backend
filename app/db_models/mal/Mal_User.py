from neomodel import UniqueIdProperty,AsyncStructuredNode, StringProperty,FloatProperty, IntegerProperty, BooleanProperty, JSONProperty, DateTimeProperty


class MalUser(AsyncStructuredNode):
    uid = UniqueIdProperty()
    user_id = IntegerProperty(unique_index=True)
    name = StringProperty(required=True)
    location = StringProperty(default='')
    joined_at = DateTimeProperty()
    num_items_watching = IntegerProperty()
    num_items_completed = IntegerProperty()
    num_items_on_hold = IntegerProperty()
    num_items_dropped = IntegerProperty()
    num_items_plan_to_watch = IntegerProperty()
    num_items = IntegerProperty()
    num_days_watched = FloatProperty()
    num_days_watching = FloatProperty()
    num_days_completed = FloatProperty()
    num_days_on_hold = FloatProperty()
    num_days_dropped = FloatProperty()
    num_days = FloatProperty()
    num_episodes = IntegerProperty()
    num_times_rewatched = IntegerProperty()
    mean_score = FloatProperty()