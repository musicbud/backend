

from .services import SpotifyAuthStrategy  
from .services import YTmusicAuthStrategy  
# from .services import AppleMusicAuthStrategy  
from .services import LastFmAuthStrategy  
from django.http import JsonResponse  
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


# Orchestrator base class
    
# Orchestrator implementations for each service strategy
class LastFmService():
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.strategy = LastFmAuthStrategy(api_key=self.api_key, api_secret=self.api_secret)

class SpotifyService():
    def __init__(self, client_id, client_secret, redirect_uri,scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.strategy = SpotifyAuthStrategy(client_id=self.client_id, client_secret=self.client_secret,
                                            redirect_uri=self.redirect_uri,scope=scope)

class YTmusicService():
    def __init__(self,client_id, client_secret,):
        self.client_id = client_id
        self.client_secret = client_secret
        self.strategy = YTmusicAuthStrategy(client_id=self.client_id, client_secret=self.client_secret)

# class AppleService():
#     def __init__(self):
#         self.strategy = AppleMusicAuthStrategy()

# Function using the Orchestrator services
def get_service(service):
        # Select the appropriate service Orchestrator
        if service == 'lastfm':
            service_instance = LastFmService(settings.LASTFM_API_KEY, settings.LASTFM_API_SECRET)
        elif service == 'spotify':
            service_instance = SpotifyService(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, settings.SPOTIFY_REDIRECT_URI,settings.SPOTIFY_SCOPE)
        elif service == 'ytmusic':
            service_instance = YTmusicService(settings.YTMUSIC_CLIENT_ID, settings.YTMUSIC_CLIENT_SECRET)
        # elif service == 'apple':
        #     service_instance = AppleService()
        else:
            return JsonResponse({'error': 'Unsupported service'}, status=400)
        return service_instance
    


