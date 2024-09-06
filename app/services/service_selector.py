import logging
from django.conf import settings
from app.services.lastfm_service import LastFmService
from app.services.ytmusic_service import YTmusicService
from app.services.mal_service import MalService
from app.services.spotify_service import SpotifyService

logger = logging.getLogger('app')

async def get_service(service_name):
    if service_name == 'spotify':
        return SpotifyService(
            settings.SPOTIFY_CLIENT_ID,
            settings.SPOTIFY_CLIENT_SECRET,
            settings.SPOTIFY_REDIRECT_URI
                            )
    elif service_name == 'lastfm':
        return LastFmService(settings.LASTFM_API_KEY, settings.LASTFM_API_SECRET)
    elif service_name == 'ytmusic':
        return YTmusicService(settings.YTMUSIC_CLIENT_ID, settings.YTMUSIC_CLIENT_SECRET, settings.YTMUSIC_REDIRECT_URI)
    elif service_name == 'mal':
        return MalService(settings.MAL_CLIENT_ID, settings.MAL_CLIENT_SECRET, settings.MAL_REDIRECT_URI)
    else:
        logger.error(f"Invalid service name: {service_name}")
        return None


