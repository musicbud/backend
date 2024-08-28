from neomodel import StructuredNode, StringProperty, UniqueIdProperty, RelationshipTo

class ParentUser(StructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique=True, required=True)
    email = StringProperty(unique=True, required=True)
    password = StringProperty(required=True)

    spotify_account = RelationshipTo('app.db_models.user.User', 'CONNECTED_TO_SPOTIFY')
    ytmusic_account = RelationshipTo('app.db_models.user.User', 'CONNECTED_TO_YTMUSIC')
    lastfm_account = RelationshipTo('app.db_models.user.User', 'CONNECTED_TO_LASTFM')
    mal_account = RelationshipTo('app.db_models.user.User', 'CONNECTED_TO_MAL')

    @classmethod
    def create_user(cls, username, email, password):
        return cls(username=username, email=email, password=password).save()