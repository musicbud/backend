from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from chat.models import Channel, Invitation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def channel_dashboard(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if request.user != channel.admin and request.user not in channel.moderators.all():
        return redirect('home')
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
