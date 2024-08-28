from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Message, Channel
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def user_list(request):
    users = ParentUser.objects.exclude(username=request.user.username)
    return render(request, 'chat/user_list.html', {'users': users})

@login_required
def chat_with_user(request, username):
    # Add logic to handle chat with a specific user
    return render(request, 'chat/chat.html', {'username': username})

@login_required
def channel_list(request):
    channels = Channel.objects.filter(members=request.user)
    return render(request, 'chat/channel_list.html', {'channels': channels})

@login_required
def channel_chat(request, channel_name):
    channel = get_object_or_404(Channel, name=channel_name)
    messages = Message.objects.filter(channel=channel).order_by('timestamp')
    return render(request, 'chat/channel_chat.html', {'channel': channel, 'messages': messages})

@login_required
def user_chat(request, username):
    recipient = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(recipient=recipient)) |
        (models.Q(sender=recipient) & models.Q(recipient=request.user))
    ).order_by('timestamp')
    return render(request, 'chat/user_chat.html', {'recipient': recipient, 'messages': messages})

def chat_view(request):
    context = {
        'test_message': 'This is a test message from the view.',
    }
    return render(request, 'chat/chat_test.html', context)

def chat_home(request):
    return render(request, 'chat/home.html')

def chat_channel(request):
    return render(request, 'chat/channel.html')

def chat_user(request):
    return render(request, 'chat/user.html')

def home(request):
    return render(request, 'chat/home.html')

def channel_list(request):
    channels = Channel.objects.all()
    return render(request, 'chat/channel_list.html', {'channels': channels})

def user_list(request):
    User = get_user_model()
    users = User.objects.all()
    return render(request, 'chat/user_list.html', {'users': users})

def chat_in_channel(request, channel_id):
    # Add logic to handle chat in a specific channel
    return render(request, 'chat/chat.html', {'channel_id': channel_id})
