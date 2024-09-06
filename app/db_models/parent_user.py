from neomodel import AsyncStructuredNode, StringProperty, UniqueIdProperty, AsyncRelationshipTo, DateTimeProperty

class ParentUser(AsyncStructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique=True, required=True)
    email = StringProperty(unique=True, required=True)
    access_token = StringProperty()
    token_created_at = DateTimeProperty()

    spotify_account = AsyncRelationshipTo('app.db_models.spotify.spotify_user.SpotifyUser', 'CONNECTED_TO_SPOTIFY')
    ytmusic_account = AsyncRelationshipTo('app.db_models.ytmusic.ytmusic_user.YtmusicUser', 'CONNECTED_TO_YTMUSIC')
    lastfm_account = AsyncRelationshipTo('app.db_models.lastfm.lastfm_user.LastfmUser', 'CONNECTED_TO_LASTFM')
    mal_account = AsyncRelationshipTo('app.db_models.mal.mal_user.MalUser', 'CONNECTED_TO_MAL')
    imdb_account = AsyncRelationshipTo('app.db_models.imdb.imdb_user.ImdbUser', 'CONNECTED_TO_IMDB')

    def __str__(self):
        return f"ParentUser(username={self.username}, uid={self.uid})"

    @classmethod
    async def create_user(cls, username, email, access_token):
        user = cls(username=username, email=email, access_token=access_token)
        await user.save()
        return user

    @classmethod
    async def get_user_by_token(cls, access_token):
        return await cls.nodes.get_or_none(access_token=access_token)
    
    @classmethod
    def create_or_update(cls, user_data):
        try:
            user = cls.nodes.get(username=user_data['username'])
            # Update existing user
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()
            return user, False
        except cls.DoesNotExist:
            # Create new user
            user = cls(**user_data)
            user.save()
            return user, True