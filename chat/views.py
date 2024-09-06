from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponse
from .models import Message, Channel, Invitation, ChatMessage
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q
import logging
from .forms import ChannelForm  # Add this line
from rest_framework.authtoken.models import Token
from asgiref.sync import sync_to_async
from django.http import HttpResponse
import json
from functools import wraps
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.http import QueryDict, JsonResponse

User = get_user_model()

logger = logging.getLogger(__name__)

def read_request_body(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    body = request.body.decode('utf-8')
                    print("Raw request body (decorator):", body)
                    request.JSON = json.loads(body)
                    # Convert JSON data to QueryDict for consistency
                    request.POST = QueryDict('', mutable=True)
                    request.POST.update(request.JSON)
                except json.JSONDecodeError as e:
                    print("Failed to parse JSON data (decorator):", str(e))
                    return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
            else:
                # For non-JSON content types, keep the original POST data
                request.JSON = None

        response = view_func(request, *args, **kwargs)

        # If the content type is application/json, ensure the response is JSON
        if 'application/json' in content_type:
            if isinstance(response, HttpResponse) and not isinstance(response, JsonResponse):
                try:
                    data = json.loads(response.content)
                    return JsonResponse(data)
                except json.JSONDecodeError:
                    return JsonResponse({'status': 'error', 'message': 'Unable to serialize response to JSON'}, status=500)

        return response
    return wrapper

@login_required
@read_request_body
def chat_home(request):
    return render(request, 'chat/home.html')

@login_required
@read_request_body
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/user_list.html', {'users': users})

@login_required
@read_request_body
def channel_list(request):
    channels = Channel.objects.all()
    return render(request, 'chat/channel_list.html', {'channels': channels})

@login_required
@read_request_body
def channel_chat(request, channel_name):
    channel = Channel.objects.get(name=channel_name)
    messages = ChatMessage.objects.filter(channel=channel)
    return render(request, 'chat/channel_chat.html', {
        'channel': channel,
        'messages': messages
    })

@login_required
@read_request_body
def user_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    return render(request, 'chat/user_chat.html', {'other_user': other_user})

@login_required
@require_POST
@csrf_exempt
@read_request_body
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

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
@read_request_body
def create_channel(request):
    if request.method == 'POST':
        form = ChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.created_by = request.user
            channel.save()
            return redirect('chat:room', room_name=channel.name)
    else:
        form = ChannelForm()
    return render(request, 'chat/create_channel.html', {'form': form})

@login_required
@require_POST
@read_request_body
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
@read_request_body
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
@read_request_body
def channel_dashboard(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if request.user != channel.admin and request.user not in channel.moderators.all():
        return redirect('home')  # or wherever you want to redirect non-admins/mods
    return render(request, 'chat/channel_admin.html', {'channel': channel})

@login_required
@read_request_body
def accept_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.members.add(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
@read_request_body
def kick_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.members.remove(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
@read_request_body
def block_user(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin or request.user in channel.moderators.all():
        channel.blocked_users.add(user)
        channel.members.remove(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
@read_request_body
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user == message.channel.admin or request.user in message.channel.moderators.all():
        message.is_deleted = True
        message.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@login_required
@read_request_body
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
@read_request_body
def add_moderator(request, channel_id, user_id):
    channel = get_object_or_404(Channel, id=channel_id)
    user = get_object_or_404(User, id=user_id)
    if request.user == channel.admin:
        channel.moderators.add(user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'})

@sync_to_async
def async_render(request, template_name, context=None):
    return render(request, template_name, context)

async def channel_list(request):
    channels = await sync_to_async(list)(Channel.objects.all())
    context = {'channels': channels}
    return await async_render(request, 'chat/channel_list.html', context)

# Keep other views synchronous for now
@read_request_body
def chat_home(request):
    return render(request, 'chat/home.html')

@read_request_body
def chat_room(request, room_name):
    messages = Message.objects.filter(room=room_name).order_by('-timestamp')[:50]
    return render(request, 'chat/channel_chat.html', {
        'room_name': room_name,
        'messages': messages,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
    })

@read_request_body
def channel_list(request):
    channels = Channel.objects.all()
    return render(request, 'chat/channel_list.html', {'channels': channels})

# @login_required
# def chat_room(request, room_name):
#     return render(request, 'chat/room.html', {
#         'room_name': room_name,
#         'username': request.user.username,
#     })

