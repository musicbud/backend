from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from .models import Message, Channel, Invitation, ChatMessage
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q
import logging
from .forms import ChannelForm  # Add this line
from rest_framework.authtoken.models import Token

User = get_user_model()

logger = logging.getLogger(__name__)

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
def channel_chat(request, channel_name):
    channel = Channel.objects.get(name=channel_name)
    messages = ChatMessage.objects.filter(channel=channel)
    return render(request, 'chat/channel_chat.html', {
        'channel': channel,
        'messages': messages
    })

@login_required
def user_chat(request, username):
    recipient = get_object_or_404(User, username=username)
    channel_name = f"chat_{min(request.user.id, recipient.id)}_{max(request.user.id, recipient.id)}"
    
    channel, created = Channel.objects.get_or_create(name=channel_name)
    
    # Ensure both users are members of the channel
    channel.members.add(request.user, recipient)
    
    messages = ChatMessage.objects.filter(channel=channel).order_by('timestamp')
    
    context = {
        'recipient': recipient,
        'channel_name': channel_name,
        'messages': messages,
    }
    
    return render(request, 'chat/user_chat.html', context)

@login_required
@require_POST
@csrf_exempt
def send_message(request):
    content = request.POST.get('content')
    recipient_type = request.POST.get('recipient_type')
    recipient_id = request.POST.get('recipient_id')

    if recipient_type == 'user':
        recipient = get_object_or_404(User, id=recipient_id)
        channel_name = f"chat_{min(request.user.id, recipient.id)}_{max(request.user.id, recipient.id)}"
        channel, _ = Channel.objects.get_or_create(name=channel_name)
        message = Message.objects.create(user=request.user, recipient=recipient, content=content, channel=channel)
    elif recipient_type == 'channel':
        channel = get_object_or_404(Channel, id=recipient_id)
        message = Message.objects.create(user=request.user, channel=channel, content=content)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid recipient type'})

    return JsonResponse({'status': 'success', 'message': 'Message sent'})
@login_required
def create_channel(request):
    if request.method == 'POST':
        form = ChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.admin = request.user
            channel.save()
            channel.members.add(request.user)
            return redirect('channel_chat', room_name=channel.name)
    else:
        form = ChannelForm()
    return render(request, 'chat/create_channel.html', {'form': form})

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

@login_required
@require_POST
def channel_action(request, channel_id, action):
    try:
        channel = Channel.objects.get(id=channel_id)
        user = request.user

        if action == 'invite':
            if channel.is_admin(user):
                invite_user_id = request.POST.get('user_id')
                invite_user = User.objects.get(id=invite_user_id)
                channel.invite_user(invite_user)
                return JsonResponse({'status': 'success', 'message': 'User invited'})

        elif action == 'accept_invitation':
            channel.accept_invitation(user)
            return JsonResponse({'status': 'success', 'message': 'Invitation accepted'})

        elif action == 'kick':
            if channel.is_admin(user):
                kick_user_id = request.POST.get('user_id')
                kick_user = User.objects.get(id=kick_user_id)
                channel.kick_user(kick_user)
                return JsonResponse({'status': 'success', 'message': 'User kicked'})

        elif action == 'block':
            if channel.is_admin(user):
                block_user_id = request.POST.get('user_id')
                block_user = User.objects.get(id=block_user_id)
                channel.block_user(block_user)
                return JsonResponse({'status': 'success', 'message': 'User blocked'})

        elif action == 'make_moderator':
            if channel.is_admin(user):
                mod_user_id = request.POST.get('user_id')
                mod_user = User.objects.get(id=mod_user_id)
                channel.make_moderator(mod_user)
                return JsonResponse({'status': 'success', 'message': 'User made moderator'})

        elif action == 'delete_message':
            if channel.is_admin(user) or channel.is_moderator(user):
                message_id = request.POST.get('message_id')
                message = Message.objects.get(id=message_id, channel=channel)
                message.delete_message()
                return JsonResponse({'status': 'success', 'message': 'Message deleted'})

        return JsonResponse({'status': 'error', 'message': 'Invalid action or permissions'}, status=400)

    except Channel.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Channel not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def channel_dashboard(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if request.user != channel.admin and request.user not in channel.moderators.all():
        return redirect('home')  # or wherever you want to redirect non-admins/mods
    return render(request, 'chat/channel_admin.html', {'channel': channel})

@login_required
def accept_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.members.add(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
def kick_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.members.remove(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
def block_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.blocked_users.add(user)
        channel.members.remove(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user == message.channel.admin or request.user in message.channel.moderators.all():
        message.is_deleted = True
        message.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
def handle_invitation(request, invitation_id, action):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    if request.user == invitation.channel.admin or request.user in invitation.channel.moderators.all():
        if action == 'accept':
            invitation.status = 'accepted'
            invitation.channel.members.add(invitation.user)
        elif action == 'decline':
            invitation.status = 'declined'
        invitation.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
def add_moderator(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin:
        channel.moderators.add(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

def chat_room(request, room_name):
    messages = Message.objects.filter(room=room_name).order_by('-timestamp')[:50]
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'messages': messages
    })
