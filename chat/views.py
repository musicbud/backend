from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .models import Message, Channel

@login_required
def user_list(request):
    users = User.objects.exclude(username=request.user.username)
    return render(request, 'chat/user_list.html', {'users': users})

@login_required
def chat_with_user(request, username):
    recipient = get_object_or_404(User, username=username)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, recipient=recipient, content=content)
            return redirect('chat_with_user', username=username)
    messages = Message.objects.filter(sender=request.user, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=request.user)
    messages = messages.order_by('timestamp')
    return render(request, 'chat/chat.html', {'recipient': recipient, 'messages': messages})

@login_required
def channel_list(request):
    channels = Channel.objects.filter(members=request.user)
    return render(request, 'chat/channel_list.html', {'channels': channels})

@login_required
def chat_in_channel(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, channel=channel, content=content)
            return redirect('chat_in_channel', channel_id=channel_id)
    messages = channel.messages.order_by('timestamp')
    return render(request, 'chat/chat.html', {'channel': channel, 'messages': messages})
