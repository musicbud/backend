from neomodel import UniqueIdProperty,AsyncStructuredNode, StringProperty, IntegerProperty,AsyncRelationshipTo


class Manga(AsyncStructuredNode):
    uid = UniqueIdProperty()
    manga_id = IntegerProperty(unique_index=True)
    title = StringProperty(required=True)
    list_status = AsyncRelationshipTo('list_status', 'HAS_STATUS')

    main_picture = AsyncRelationshipTo('.main_picture.MainPicture', 'HAS_PICTURE')

    async def serialize(self):

        main_pictures = await self.main_picture.all()

        return {
            'uid': self.uid,
            'manga_id': self.manga_id,
            'title': self.title,
            'main_picture': [await main_picture.serialize() for main_picture in main_pictures] if main_pictures else [],
        }
    