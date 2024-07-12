from django.http import JsonResponse
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist
from django.http import JsonResponse

from ..db_models.User import User
from ..db_models.spotify.Spotify_User import SpotifyUser
from ..db_models.lastfm.Lastfm_User import LastfmUser
from ..db_models.ytmusic.Ytmusic_User import YtmusicUser

from ..services.ServiceSelector import get_service
import logging

logger = logging.getLogger(__name__)

def login(request):
    service = request.GET.get('service', 'spotify')  # Default to 'lastfm' if no service is specified
    try:
        authorization_link = get_service(service).create_authorize_url()
        return JsonResponse({
            'message': 'Generated authorization link successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'authorization_link': authorization_link}
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)

def ytmusic_callback(request):
    try:
        service = request.GET.get('service', 'ytmusic')  
        code = request.GET.get('code')
        tokens = get_service(service).get_tokens(code=code)
        user_profile = get_service(service).get_user_profile(tokens)

        try:
            user = YtmusicUser.nodes.get(channel_handle=user_profile['channelHandle'])
        except MultipleNodesReturned:
            return JsonResponse({'error': 'Multiple users found with this uid'}, status=500)
        except DoesNotExist:
            user = YtmusicUser.create_from_ytmusic_profile(user_profile,tokens)

        updated_user = YtmusicUser.update_ytmusic_tokens(user_profile,tokens)
        if updated_user is None:
            return JsonResponse({'error': 'Error updating tokens'}, status=500)

        return JsonResponse({
            'message': 'logged in successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data':  tokens,
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)
    
def spotify_callback(request):
    try:
        code = request.GET.get('code')
        service = 'spotify'
        
        tokens = get_service(service).get_tokens(code)

        user_profile = get_service(service).get_user_profile(tokens)
        try:
            user = SpotifyUser.nodes.get(spotify_id=user_profile['id'])
        except MultipleNodesReturned:
            return JsonResponse({'error': 'Multiple users found with this uid'}, status=500)
        except DoesNotExist:
            user = SpotifyUser.create_from_spotify_profile(user_profile,tokens)

        updated_user = SpotifyUser.update_spotify_tokens(user,tokens)
        if updated_user is None:
            return JsonResponse({'error': 'Error updating tokens'}, status=500)

        return JsonResponse({
            'message': 'logged in successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': tokens
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)
    

def lastfm_callback(request):
    try:
        service = 'lastfm'
        token = request.GET.get('token')
        if not token:
            return JsonResponse({'error': 'Token not provided'}, status=400)

        user_profile = get_service(service).get_user_profile(token)
        try:
            user = LastfmUser.nodes.get(username=user_profile['username'])
        except MultipleNodesReturned:
            return JsonResponse({'error': 'Multiple users found with this username'}, status=500)
        except DoesNotExist:
            user = LastfmUser.create_from_lastfm_profile(user_profile,token)

        updated_user = LastfmUser.update_lastfm_tokens(user, token)
        if not updated_user:
            return JsonResponse({'error': 'Error updating user tokens'}, status=500)

        return JsonResponse({
            'message': 'Logged in successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'accessToken': token}
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def not_found_view(request, exception):
    return JsonResponse({'error': 'Resource not found on this server'}, status=404)

def error_view(request):
    return JsonResponse({'error': 'Internal Server Error'}, status=500)
