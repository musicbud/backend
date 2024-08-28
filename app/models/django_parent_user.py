from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, IntegrityError
from ..managers import CustomUserManager
from ..db_models.parent_user import ParentUser
from django.db.models.signals import post_save
from django.dispatch import receiver
import asyncio
from neomodel import db

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
        try:
            db.cypher_query(
                """
                MERGE (u:ParentUser {username: $username})
                ON CREATE SET u.email = $email, u.password = $password
                ON MATCH SET u.email = $email, u.password = $password
                """,
                {
                    'username': self.username,
                    'email': self.email,
                    'password': self.password
                }
            )
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
