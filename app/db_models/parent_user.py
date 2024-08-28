from neomodel import StructuredNode, StringProperty, BooleanProperty, UniqueIdProperty, RelationshipTo
from django.contrib.auth import get_user_model

DjangoParentUser = get_user_model()

class ParentUser(StructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    is_active = BooleanProperty(default=False)

    spotify_account = RelationshipTo('.user.User', 'CONNECTED_TO_SPOTIFY')
    ytmusic_account = RelationshipTo('.user.User', 'CONNECTED_TO_YTMUSIC')
    lastfm_account = RelationshipTo('.user.User', 'CONNECTED_TO_LASTFM')
    mal_account = RelationshipTo('.user.User', 'CONNECTED_TO_MAL')

    @classmethod
    def create_from_django_user(cls, django_user):
        return cls(
            username=django_user.username,
            email=django_user.email,
            is_active=django_user.is_active
        ).save()

    @classmethod
    def get_or_create(cls, django_user):
        try:
            return cls.nodes.get(username=django_user.username)
        except cls.DoesNotExist:
            return cls.create_from_django_user(django_user)