from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from ..managers import CustomUserManager
from ..db_models.parent_user import ParentUser
from django.db.models.signals import post_save
from django.dispatch import receiver
import asyncio
from rest_framework_simplejwt.tokens import RefreshToken
from app.services.spotify_service import SpotifyService
from app.services.ytmusic_service import YTmusicService
from app.services.lastfm_service import LastFmService
from django.conf import settings
from asgiref.sync import sync_to_async
from django.db import transaction
from django.core.cache import cache

class DjangoParentUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    token_created_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @transaction.atomic
    def get_tokens(self):
        refresh = RefreshToken.for_user(self)
        access_token = str(refresh.access_token)
        
        self.access_token = access_token
        self.token_created_at = timezone.now()
        self.save()

        # Trigger async sync_to_neo4j
        transaction.on_commit(lambda: async_to_sync(self.sync_to_neo4j)())

        return {
            'refresh': str(refresh),
            'access': access_token,
        }

    async def sync_to_neo4j(self):
        # Use a cache lock to prevent multiple syncs for the same user
        lock_key = f"sync_lock_{self.id}"
        if cache.add(lock_key, "locked", timeout=300):  # 5 minutes timeout
            try:
                # Use sync_to_async to wrap the synchronous database operations
                get_or_create_parent_user = sync_to_async(self._get_or_create_parent_user)
                parent_user = await get_or_create_parent_user()

                # Sync Spotify
                spotify_user = await sync_to_async(parent_user.spotify_account.get)()
                if spotify_user:
                    await SpotifyService(
                        client_id=settings.SPOTIFY_CLIENT_ID,
                        client_secret=settings.SPOTIFY_CLIENT_SECRET,
                        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                        scope=settings.SPOTIFY_SCOPE
                    ).save_user_likes(spotify_user)

                # Sync YTMusic
                ytmusic_user = await sync_to_async(parent_user.ytmusic_account.get)()
                if ytmusic_user:
                    await YTmusicService(
                        client_id=settings.YTMUSIC_CLIENT_ID,
                        client_secret=settings.YTMUSIC_CLIENT_SECRET,
                        redirect_uri=settings.YTMUSIC_REDIRECT_URI
                    ).save_user_likes(ytmusic_user)

                # Sync Last.fm
                lastfm_user = await sync_to_async(parent_user.lastfm_account.get)()
                if lastfm_user:
                    await LastFmService(
                        api_key=settings.LASTFM_API_KEY,
                        api_secret=settings.LASTFM_API_SECRET
                    ).save_user_likes(lastfm_user)
            finally:
                cache.delete(lock_key)

    def _get_or_create_parent_user(self):
        parent_user, created = ParentUser.objects.get_or_create(
            username=self.username,
            defaults={'email': self.email, 'access_token': self.access_token}
        )
        if not created:
            parent_user.access_token = self.access_token
            parent_user.token_created_at = self.token_created_at
            parent_user.save()
        return parent_user

# Remove the post_save signal
# @receiver(post_save, sender=DjangoParentUser)
# def sync_user_to_neo4j(sender, instance, created, **kwargs):
#     asyncio.run(instance.sync_to_neo4j())
