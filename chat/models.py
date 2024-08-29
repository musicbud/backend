from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)  # Add this line
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_channels', null=True)
    members = models.ManyToManyField(User, related_name='channels')
    moderators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='moderated_channels')
    blocked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='blocked_channels')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    author = models.ForeignKey(User, related_name='authored_messages', on_delete=models.CASCADE)
    room = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'

class Invitation(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
            return f'{self.user.username} - {self.channel.name} ({self.status})'

class ChatMessage(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
