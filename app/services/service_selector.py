

from .lastfm_service import LastFmService
from .spotify_service import SpotifyService
from .ytmusic_service import YTmusicService 
from .mal_service import MalService 

from django.http import JsonResponse  
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
# Function using the Orchestrator services
def get_service(service, request=None):
        # Select the appropriate service Orchestrator
        if service == 'lastfm':
            service_instance = LastFmService(settings.LASTFM_API_KEY, settings.LASTFM_API_SECRET)
        elif service == 'spotify':
            service_instance = SpotifyService(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, settings.SPOTIFY_REDIRECT_URI,settings.SPOTIFY_SCOPE)
        elif service == 'ytmusic':
            service_instance = YTmusicService(settings.YTMUSIC_CLIENT_ID, settings.YTMUSIC_CLIENT_SECRET, settings.YTMUSIC_REDIRECT_URI)
        elif service == 'mal':
            service_instance = MalService(settings.MAL_CLIENT_ID, settings.MAL_CLIENT_SECRET, settings.MAL_REDIRECT_URI,settings.MAL_SCOPE,request)
        else:
            return JsonResponse({'error': 'Unsupported service'}, status=400)
        return service_instance
    


