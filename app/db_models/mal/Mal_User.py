from datetime import datetime
from neomodel import  StringProperty,AsyncRelationshipTo,FloatProperty, AsyncRelationshipFrom,IntegerProperty, BooleanProperty, JSONProperty, DateTimeProperty
from ..User import User

class MalUser(User):
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
    access_token = StringProperty()

    top_anime = AsyncRelationshipTo('.Mal_Anime.Anime', 'TOP_ANIME')
    top_manga = AsyncRelationshipTo('.Mal_Manga.Manga', 'TOP_MANGA')


    parent = AsyncRelationshipFrom('..Parent_User.ParentUser', 'CONNECTED_TO_MAL')


    async def create_from_mal_profile(user_info,access_token):
        anime_statistics = user_info.get('anime_statistics', {})
        user = MalUser()

        user.user_id= user_info['id']
        user.name= user_info['name']
        user.location = user_info.get('location', '')
        user.joined_at= datetime.strptime(user_info['joined_at'], '%Y-%m-%dT%H:%M:%S%z')
        user.num_items_watching= anime_statistics.get('num_items_watching', 0)
        user.num_items_completed= anime_statistics.get('num_items_completed', 0)
        user.num_items_on_hold= anime_statistics.get('num_items_on_hold', 0)
        user.num_items_dropped= anime_statistics.get('num_items_dropped', 0)
        user.num_items_plan_to_watch= anime_statistics.get('num_items_plan_to_watch', 0)
        user.num_items= anime_statistics.get('num_items', 0)
        user.num_days_watched= anime_statistics.get('num_days_watched', 0.0)
        user.num_days_watching= anime_statistics.get('num_days_watching', 0.0)
        user.num_days_completed= anime_statistics.get('num_days_completed', 0.0)
        user.num_days_on_hold= anime_statistics.get('num_days_on_hold', 0.0)
        user.num_days_dropped= anime_statistics.get('num_days_dropped', 0.0)
        user.num_days= anime_statistics.get('num_days', 0.0)
        user.num_episodes= anime_statistics.get('num_episodes', 0)
        user.num_times_rewatched= anime_statistics.get('num_times_rewatched', 0)
        user.mean_score= anime_statistics.get('mean_score', 0.0)
        user.access_token=access_token
        user.service = 'mal'

    

        await user.save()
