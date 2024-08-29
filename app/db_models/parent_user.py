from neomodel import StructuredNode, StringProperty, UniqueIdProperty, RelationshipTo, DateTimeProperty

class ParentUser(StructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique=True, required=True)
    email = StringProperty(unique=True, required=True)
    access_token = StringProperty()
    token_created_at = DateTimeProperty()

    spotify_account = RelationshipTo('app.db_models.spotify.spotify_user.SpotifyUser', 'CONNECTED_TO_SPOTIFY')
    ytmusic_account = RelationshipTo('app.db_models.ytmusic.ytmusic_user.YtmusicUser', 'CONNECTED_TO_YTMUSIC')
    lastfm_account = RelationshipTo('app.db_models.lastfm.lastfm_user.LastfmUser', 'CONNECTED_TO_LASTFM')
    mal_account = RelationshipTo('app.db_models.mal.mal_user.MalUser', 'CONNECTED_TO_MAL')

    @classmethod
    async def create_user(cls, username, email, access_token):
        user = cls(username=username, email=email, access_token=access_token)
        await user.save()
        return user

    @classmethod
    async def get_user_by_token(cls, access_token):
        return await cls.nodes.get_or_none(access_token=access_token)