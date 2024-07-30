from neomodel import UniqueIdProperty,AsyncStructuredNode, StringProperty, IntegerProperty,AsyncRelationshipTo


class Manga(AsyncStructuredNode):
    uid = UniqueIdProperty()
    manga_id = IntegerProperty(unique_index=True)
    title = StringProperty(required=True)
    main_picture = AsyncRelationshipTo('MainPicture', 'HAS_PICTURE')
    list_status = AsyncRelationshipTo('ListStatus', 'HAS_STATUS')