from neomodel import UniqueIdProperty,AsyncRelationshipTo,AsyncStructuredNode, StringProperty, IntegerProperty, BooleanProperty, JSONProperty, DateTimeProperty

class Anime(AsyncStructuredNode):
    uid = UniqueIdProperty()
    anime_id = IntegerProperty(unique_index=True)
    title = StringProperty(required=True)
    status = StringProperty()
    score = IntegerProperty(default=0)
    num_watched_episodes = IntegerProperty(default=0)
    is_rewatching = BooleanProperty(default=False)
    updated_at = DateTimeProperty()

    main_picture = AsyncRelationshipTo('.main_picture.MainPicture', 'HAS_PICTURE')


    async def serialize(self):

        main_pictures = await self.main_picture.all()

        return {
            'uid': self.uid,
            'anime_id': self.anime_id,
            'title': self.title,
            'main_picture': [await main_picture.serialize() for main_picture in main_pictures] if main_pictures else [],
        }
    