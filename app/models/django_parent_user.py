from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, IntegrityError
from ..managers import CustomUserManager
from ..db_models.parent_user import ParentUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from neomodel import db
import asyncio
from rest_framework_simplejwt.tokens import RefreshToken

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

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    async def sync_to_neo4j(self):
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

    @classmethod
    async def create_user(cls, username, email, password, **extra_fields):
        try:
            user = await cls.objects.acreate_user(username=username, email=email, password=password, **extra_fields)
            await user.sync_to_neo4j()
            return user, None
        except IntegrityError as e:
            return None, str(e)

@receiver(post_save, sender=DjangoParentUser)
def sync_user_to_neo4j(sender, instance, created, **kwargs):
    asyncio.run(instance.sync_to_neo4j())
