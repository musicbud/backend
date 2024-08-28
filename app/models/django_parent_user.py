from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, IntegrityError
from ..managers import CustomUserManager
from ..db_models.parent_user import ParentUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from neomodel import db
import asyncio

class DjangoParentUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def sync_to_neo4j(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._sync_to_neo4j_async())
        finally:
            loop.close()

    async def _sync_to_neo4j_async(self):
        try:
            neo4j_user = await ParentUser.nodes.get_or_none(username=self.username)
            if neo4j_user is None:
                neo4j_user = ParentUser(username=self.username)
                created = True
            else:
                created = False
            
            neo4j_user.email = self.email
            neo4j_user.password = self.password
            await neo4j_user.save()
            print(f"User {'created' if created else 'updated'} in Neo4j: {self.username}")
        except Exception as e:
            print(f"Error syncing to Neo4j: {e}")

@receiver(post_save, sender=DjangoParentUser)
def sync_user_to_neo4j(sender, instance, created, **kwargs):
    instance.sync_to_neo4j()

@classmethod
def create_user(cls, username, email, password, **extra_fields):
    try:
        user = cls.objects.create_user(username=username, email=email, password=password, **extra_fields)
        return user, None
    except IntegrityError as e:
        return None, str(e)
