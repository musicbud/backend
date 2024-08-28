from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Channel(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='channels')

    def __str__(self):
        return self.name

    @classmethod
    def create_channel(cls, name, creator):
        channel = cls.objects.create(name=name)
        channel.members.add(creator)
        return channel

    def add_member(self, user):
        self.members.add(user)


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)

    def __str__(self):
        return f'Message from {self.sender} to {self.recipient if self.recipient else self.channel}'

    @classmethod
    def send_message_to_user(cls, sender, recipient, content):
        return cls.objects.create(sender=sender, recipient=recipient, content=content)

    @classmethod
    def send_message_to_channel(cls, sender, channel, content):
        return cls.objects.create(sender=sender, channel=channel, content=content)

