import time
import logging
from .ServiceStrategy import ServiceStrategy
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import asyncio
import ytmusicapi

from app.db_models.ytmusic.Ytmusic_Artist import YtmusicArtist
from app.db_models.ytmusic.Ytmusic_Track import YtmusicTrack
from app.db_models.ytmusic.Ytmusic_Album import YtmusicAlbum

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

class YTmusicService(ServiceStrategy):
    """
    A class to interact with YouTube Music's API and integrate data into a Neo4j database.
    """
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initializes the YouTube Music API client.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.executor = ThreadPoolExecutor()
        logger.info("YTmusicService initialized")

    async def create_authorize_url(self) -> str:
        logger.info("Creating authorize URL")
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        SCOPES = [
            "openid", 'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube'
        ]

        loop = asyncio.get_event_loop()
        auth_url = await loop.run_in_executor(self.executor, self._create_authorize_url, client_config, SCOPES)
        logger.info(f"Authorize URL created: {auth_url}")
        return auth_url

    def _create_authorize_url(self, client_config: Dict, SCOPES: List[str]) -> str:
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES, redirect_uri=self.redirect_uri)
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    async def get_tokens(self, code: str) -> Dict:
        logger.info("Getting tokens")
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        SCOPES = [
            "openid", 'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube'
        ]

        loop = asyncio.get_event_loop()
        tokens = await loop.run_in_executor(self.executor, self._get_tokens, client_config, SCOPES, code)
        logger.info("Tokens retrieved successfully")
        return tokens

    def _get_tokens(self, client_config: Dict, SCOPES: List[str], code: str) -> Dict:
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES, redirect_uri=self.redirect_uri)
        tokens = flow.fetch_token(code=code)
        return tokens

    async def get_user_profile(self, tokens: Dict) -> Dict:
        logger.info("Getting user profile")
        token_filtered = {
            'access_token': tokens['access_token'],
            'expires_in': tokens['expires_in'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_at': tokens['expires_at'],
            'scope': tokens['scope']
        }

        loop = asyncio.get_event_loop()
        user_profile = await loop.run_in_executor(self.executor, self._get_user_profile, token_filtered)
        logger.info("User profile retrieved successfully")
        return user_profile

    def _get_user_profile(self, token_filtered: Dict) -> Dict:
        ytmusic = ytmusicapi.YTMusic(auth=token_filtered)
        return ytmusic.get_account_info()

    async def fetch_library_artists(self, user: str) -> List[Dict]:
        logger.info(f"Fetching library artists for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        artists = await loop.run_in_executor(self.executor, ytmusic.get_library_artists)
        logger.info(f"Library artists fetched for user: {user}")
        return artists

    async def fetch_library_tracks(self, user: str) -> List[Dict]:
        logger.info(f"Fetching library tracks for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        tracks = await loop.run_in_executor(self.executor, ytmusic.get_library_songs)
        logger.info(f"Library tracks fetched for user: {user}")
        return tracks

    async def fetch_library_albums(self, user: str) -> List[Dict]:
        logger.info(f"Fetching library albums for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        albums = await loop.run_in_executor(self.executor, ytmusic.get_library_albums)
        logger.info(f"Library albums fetched for user: {user}")
        return albums

    async def fetch_liked_tracks(self, user: str) -> List[Dict]:
        logger.info(f"Fetching liked tracks for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        liked_tracks = await loop.run_in_executor(self.executor, lambda: ytmusic.get_liked_songs()['tracks'])
        logger.info(f"Liked tracks fetched for user: {user}")
        return liked_tracks

    async def fetch_library_subscriptions(self, user: str) -> List[Dict]:
        logger.info(f"Fetching library subscriptions for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        subscriptions = await loop.run_in_executor(self.executor, ytmusic.get_library_subscriptions)
        logger.info(f"Library subscriptions fetched for user: {user}")
        return subscriptions

    async def fetch_history(self, user: str) -> List[Dict]:
        logger.info(f"Fetching history for user: {user}")
        ytmusic = ytmusicapi.YTMusic(
            auth={
                'access_token': user.access_token,
                'expires_in': user.expires_in,
                'refresh_token': user.refresh_token,
                'token_type': user.token_type,
                'expires_at': user.expires_at,
                'scope': user.scope
            }
        )
        loop = asyncio.get_event_loop()
        history = await loop.run_in_executor(self.executor, ytmusic.get_history)
        logger.info(f"History fetched for user: {user}")
        return history

    async def save_user_likes(self, user: str) -> None:
        logger.info(f"Saving user likes for user: {user}")
        # Fetch user data asynchronously
        user_liked_tracks = await self.fetch_liked_tracks(user)
        user_library_subscriptions = await self.fetch_library_subscriptions(user)
        user_history = await self.fetch_history(user)

        # Map data to Neo4j asynchronously
        await asyncio.gather(
            self.map_to_neo4j(user, 'Track', user_liked_tracks, 'likes'),
            self.map_to_neo4j(user, 'Artist', user_library_subscriptions, 'likes'),
            self.map_to_neo4j(user, 'Track', user_history, 'played')
        )
        logger.info(f"User likes saved for user: {user}")

    async def map_to_neo4j(self, user: str, label: str, items: List[Dict], relation_type: str) -> None:
        logger.info(f"Mapping {label} to Neo4j for user: {user} with relation: {relation_type}")
        loop = asyncio.get_event_loop()
        tasks = []

        for item in items:
            if label == 'Artist':
                tasks.append(self._process_artist(user, item))
            elif label == 'Track':
                tasks.append(self._process_track(user, item, relation_type))

        # Execute all tasks concurrently
        await asyncio.gather(*tasks)
        logger.info(f"Mapped {label} to Neo4j for user: {user} with relation: {relation_type}")

    async def _process_artist(self, user: str, item: Dict) -> None:
        logger.info(f"Processing artist: {item['artist']} for user: {user}")
        # Check if the artist already exists
        node = await YtmusicArtist.nodes.get_or_none(name=item['artist'])
        if not node:
            logger.info(f"Creating new artist node: {item['artist']} for user: {user}")
            node = await YtmusicArtist(
                name=item['artist'],
                browseId=item['browseId'],
                subscribers=item['subscribers'],
                thumbnails=[image['url'] for image in item['thumbnails']],
                thumbnail_heights=[image['height'] for image in item['thumbnails']],
                thumbnail_widthes=[image['width'] for image in item['thumbnails']]
            ).save()

        # Connect user with artist
        await user.likes_artists.connect(node)
        logger.info(f"Connected user: {user} with artist: {item['artist']}")

    async def _process_track(self, user: str, item: Dict, relation_type: str) -> None:
        logger.info(f"Processing track: {item['title']} for user: {user} with relation: {relation_type}")
        # Check if the track already exists
        node = await YtmusicTrack.nodes.get_or_none(name=item['title'])
        if not node:
            logger.info(f"Creating new track node: {item['title']} for user: {user}")
            node = await YtmusicTrack(
                name=item['title'],
                videoId=item['videoId'],
                playlistId=item.get('playlistId', None),
                thumbnails=[image['url'] for image in item['thumbnails']],
                thumbnail_heights=[image['height'] for image in item['thumbnails']],
                thumbnail_widthes=[image['width'] for image in item['thumbnails']],
                duration=item.get('duration', None),
                album=item.get('album', None)
            ).save()

        # Connect user with track
        await getattr(user, f'{relation_type}_tracks').connect(node)
        logger.info(f"Connected user: {user} with track: {item['title']} with relation: {relation_type}")
