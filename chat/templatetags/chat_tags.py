from django import template
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='serialize_messages')
def serialize_messages(messages):
    return json.dumps([
        {
            'content': message.content,
            'username': message.author.username,
            'timestamp': message.timestamp.isoformat()
        } for message in messages
    ], cls=DjangoJSONEncoder)
