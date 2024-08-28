from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from .models import Message, Channel
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q

User = get_user_model()

@login_required
def chat_home(request):
    return render(request, 'chat/home.html')

@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'chat/user_list.html', {'users': users})

@login_required
def channel_list(request):
    channels = Channel.objects.all()
    return render(request, 'chat/channel_list.html', {'channels': channels})

@login_required
def channel_chat(request, room_name):
    channel, created = Channel.objects.get_or_create(name=room_name)
    messages = Message.objects.filter(channel=channel).order_by('timestamp')
    return render(request, 'chat/channel_chat.html', {
        'room_name': room_name,
        'channel': channel,
        'messages': messages
    })

@login_required
def user_chat(request, username):
    recipient, created = User.objects.get_or_create(username=username)
    if created:
        recipient.set_unusable_password()
        recipient.save()
    
    messages = Message.objects.filter(
        (Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user))
    ).order_by('timestamp')
    
    return render(request, 'chat/user_chat.html', {
        'recipient': recipient,
        'messages': messages,
    })

@login_required
@require_POST
@csrf_exempt
def send_message(request):
    content = request.POST.get('content')
    recipient_type = request.POST.get('recipient_type')
    recipient_id = request.POST.get('recipient_id')

    if recipient_type == 'user':
        recipient = get_object_or_404(User, id=recipient_id)
        message = Message.send_message_to_user(request.user, recipient, content)
    elif recipient_type == 'channel':
        channel = get_object_or_404(Channel, id=recipient_id)
        message = Message.send_message_to_channel(request.user, channel, content)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid recipient type'})

    return JsonResponse({'status': 'success', 'message': 'Message sent'})

@login_required
@require_POST
def create_channel(request):
    name = request.POST.get('name')
    if Channel.objects.filter(name=name).exists():
        return JsonResponse({'status': 'error', 'message': 'Channel name already exists'})
    
    channel = Channel.create_channel(name, request.user)
    return JsonResponse({'status': 'success', 'channel_id': channel.id})

@login_required
@require_POST
def add_channel_member(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    username = request.POST.get('username')
    user = get_object_or_404(User, username=username)
    
    if user in channel.members.all():
        return JsonResponse({'status': 'error', 'message': 'User is already a member of this channel'})
    
    channel.add_member(user)
    return JsonResponse({'status': 'success', 'message': 'User added to channel'})
