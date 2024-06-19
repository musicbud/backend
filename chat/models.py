from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import time
from django.contrib.auth.models import User



class Channel(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='channels')

    def __str__(self):
        return self.name
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)

    def __str__(self):
        return f'Message from {self.sender} to {self.recipient if self.recipient else self.channel}'

