import os
import logging
import asyncio
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import pylast
from app.db_models.lastfm.lastfm_artist import LastfmArtist
from app.db_models.lastfm.lastfm_track import LastfmTrack
from app.db_models.lastfm.lastfm_genre import LastfmGenre
from app.db_models.lastfm.lastfm_album import LastfmAlbum
from .service_strategy import ServiceStrategy

logger = logging.getLogger(__name__)

class LastFmService(ServiceStrategy):
    """
    An implementation of the AuthStrategy abstract base class for Last.fm API authentication and data retrieval.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the LastFmAuthService with the provided API key and secret.
        Sets up the network and session key.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_key_file = os.path.join(os.path.expanduser("~"), ".lastfm_session_key")
        self.network = pylast.LastFMNetwork(api_key=self.api_key, api_secret=self.api_secret)
        self.executor = ThreadPoolExecutor()

    async def get_user_profile(self, token: str) -> Dict[str, Any]:
        """
        Fetches the user profile using the provided token.
        """
        logger.debug("Fetching user profile")
        loop = asyncio.get_event_loop()
        network = pylast.LastFMNetwork(api_key=self.api_key, api_secret=self.api_secret, token=token)
        username = await loop.run_in_executor(self.executor, network.get_authenticated_user().get_name)
        return {'username': username}

    async def create_authorize_url(self) -> str:
        """
        Generates a URL for user authorization.
        """
        logger.debug("Creating authorization URL")
        skg = pylast.SessionKeyGenerator(self.network)
        url = skg.get_web_auth_url()  # Assuming this is a synchronous call; if async, use await
        parsed_url = urlparse(url)

        # Parse the query parameters
        query_params = parse_qs(parsed_url.query)

        # Remove the token parameter
        query_params.pop('token', None)

        # Reconstruct the query string without the token
        query_string = urlencode(query_params, doseq=True)

        # Reconstruct the full URL without the token parameter
        return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, query_string, parsed_url.fragment))

    async def fetch_top_artists(self, username: str) -> List[pylast.TopItem]:
        """
        Fetches the top artists for a given user.
        """
        logger.debug(f"Fetching top artists for user: {username}")
        loop = asyncio.get_event_loop()
        user = pylast.User(username, self.network)
        return await loop.run_in_executor(self.executor, user.get_top_artists)

    async def fetch_top_tracks(self, username: str) -> List[pylast.TopItem]:
        """
        Fetches the top tracks for a given user.
        """
        logger.debug(f"Fetching top tracks for user: {username}")
        loop = asyncio.get_event_loop()
        user = pylast.User(username, self.network)
        return await loop.run_in_executor(self.executor, user.get_top_tracks)

    async def fetch_top_genres(self, username: str) -> List[Tuple[str, int]]:
        """
        Fetches the top genres for a given user based on their top artists' tags.
        """
        logger.debug(f"Fetching top genres for user: {username}")
        top_artists = await self.fetch_top_artists(username)
        genre_count: Dict[str, int] = {}

        for artist in top_artists:
            tags = await asyncio.get_event_loop().run_in_executor(self.executor, artist.item.get_top_tags)
            for tag in tags:
                genre = tag.item.get_name()
                genre_count[genre] = genre_count.get(genre, 0) + int(tag.weight)

        # Convert dictionary to list of tuples for sorting
        sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres

    async def fetch_liked_tracks(self, username: str) -> List[pylast.Track]:
        """
        Fetches the liked tracks for a given user.
        """
        logger.debug(f"Fetching liked tracks for user: {username}")
        loop = asyncio.get_event_loop()
        user = pylast.User(username, self.network)
        return await loop.run_in_executor(self.executor, user.get_loved_tracks)

    async def fetch_recent_tracks(self, username: str) -> List[pylast.Track]:
        """
        Fetches the recent tracks for a given user.
        """
        logger.debug(f"Fetching recent tracks for user: {username}")
        loop = asyncio.get_event_loop()
        user = pylast.User(username, self.network)
        return await loop.run_in_executor(self.executor, user.get_recent_tracks)

    async def map_to_neo4j(self, user: Any, label: str, items: List[Any], relation_type: str) -> None:
        """
        Maps data to Neo4j based on the label and relation type.
        """
        logger.debug(f"Mapping data to Neo4j for user: {user}, label: {label}, relation_type: {relation_type}")
        loop = asyncio.get_event_loop()
        tasks = []

        for item in items:
            if label == 'Artist':
                tasks.append(self._process_artist(user, item, relation_type))
            elif label == 'Track':
                tasks.append(self._process_track(user, item, relation_type))
            elif label == 'Played_Track':
                tasks.append(self._process_played_track(user, item))
            elif label == 'Genre':
                tasks.append(self._process_genre(user, item, relation_type))

        # Execute all tasks concurrently
        await asyncio.gather(*tasks)

    async def _process_artist(self, user: Any, item: pylast.TopItem, relation_type: str) -> None:
        """
        Processes and saves an artist node to Neo4j, and creates relationships with the user.
        """
        logger.debug(f"Processing artist: {item.item.get_name()} for user: {user}")
        loop = asyncio.get_event_loop()
        item_name = item.item.get_name()
        item_id = item.item.get_mbid() if item.item.get_mbid() is not None else item_name
        node = await  LastfmArtist.nodes.get_or_none(name=item_name)
        if not node:
            logger.debug(f"Artist not found, creating new node: {item_name}")
            node = await  LastfmArtist(lastfm_id=item_id, name=item_name).save()

        if relation_type == "top":
            logger.debug(f"Creating relationship between user and artist: {item_name}")
            await user.top_artists.connect(node)
            await user.likes_artists.connect(node)
        elif relation_type == "liked":
            logger.debug(f"Creating relationship between user and artist: {item_name}")
            await user.likes_artists.connect(node)

    async def _process_track(self, user: Any, item: pylast.TopItem, relation_type: str) -> None:
        """
        Processes and saves a track node to Neo4j, and creates relationships with the user.
        """
        logger.debug(f"Processing track: {item.item.get_name()} for user: {user}")
        loop = asyncio.get_event_loop()
        item_name = item.item.get_name()
        item_id = item.item.get_mbid() if item.item.get_mbid() is not None else item_name
        node = await  LastfmTrack.nodes.get_or_none(name=item_name)
        if not node:
            logger.debug(f"Track not found, creating new node: {item_name}")
            node = await  LastfmTrack(lastfm_id=item_id, name=item_name).save()

        if relation_type == "top":
            if not await self._relationship_exists(user, node, 'top_tracks'):
                logger.debug(f"Creating relationship between user and track: {item_name}")
                await  user.top_tracks.connect(node)
                await  user.likes_tracks.connect(node)
        elif relation_type == "liked":
            if not await self._relationship_exists(user, node, 'likes_tracks'):
                logger.debug(f"Creating relationship between user and track: {item_name}")
                await  user.likes_tracks.connect(node)

    async def _process_played_track(self, user: Any, item: pylast.Track) -> None:
        """
        Processes and saves a played track node to Neo4j, and creates a relationship with the user.
        """
        logger.debug(f"Processing played track: {item.track.get_name()} for user: {user}")
        loop = asyncio.get_event_loop()
        track_name = item.track.get_name()
        node = await  LastfmTrack.nodes.get_or_none(name=track_name)
        if not node:
            logger.debug(f"Played track not found, creating new node: {track_name}")
            node = await  LastfmTrack(name=track_name).save()
        if not await self._relationship_exists(user, node, 'played_tracks'):
            logger.debug(f"Creating relationship between user and played track: {track_name}")
            await  user.played_tracks.connect(node)

    async def _process_genre(self, user: Any, item: Tuple[str, int], relation_type: str) -> None:
        """
        Processes and saves a genre node to Neo4j, and creates relationships with the user.
        """
        logger.debug(f"Processing genre: {item[0]} for user: {user}")
        item_name = item[0]
        node = await  LastfmGenre.nodes.get_or_none(name=item_name)
        if not node:
            logger.debug(f"Genre not found, creating new node: {item_name}")
            node = await  LastfmGenre(name=item_name).save()
        if relation_type == "top":
                logger.debug(f"Creating relationship between user and genre: {item_name}")
                await  user.top_genres.connect(node)
                await  user.likes_genres.connect(node)
        elif relation_type == "liked":
                logger.debug(f"Creating relationship between user and genre: {item_name}")
                await  user.likes_genres.connect(node)

    async def clear_user_likes(self, user: Any) -> None:
        """
        Clears the user's existing likes in Neo4j.
        """
        logger.debug(f"Clearing user likes for user: {user.username}")

        # Disconnect existing relationships
        await asyncio.gather(
            user.top_artists.disconnect_all(),
            user.top_tracks.disconnect_all(),
            user.top_genres.disconnect_all(),
            user.likes_tracks.disconnect_all(),
            user.likes_artists.disconnect_all(),
            user.likes_genres.disconnect_all(),
            user.played_tracks.disconnect_all()
        )
        logger.debug("User likes cleared successfully")
   

    async def save_user_likes(self, user: Any) -> None:
        """
        Fetches and saves the user's top artists, tracks, genres, liked tracks, and recent tracks to Neo4j.
        """
        logger.debug(f"Saving user likes for user: {user.username}")

        # Clear existing user likes
        await self.clear_user_likes(user)
        
        user_top_artists = await self.fetch_top_artists(user.username)
        user_top_tracks = await self.fetch_top_tracks(user.username)
        user_top_genres = await self.fetch_top_genres(user.username)
        user_liked_tracks = await self.fetch_liked_tracks(user.username)
        user_played_tracks = await self.fetch_recent_tracks(user.username)
        
        # # Map data to Neo4j
        await asyncio.gather(
            self.map_to_neo4j(user, 'Artist', user_top_artists, "top"),
            self.map_to_neo4j(user, 'Track', user_top_tracks, "top"),
            self.map_to_neo4j(user, 'Genre', user_top_genres, "top"),
            self.map_to_neo4j(user, 'Track', user_liked_tracks, "liked"),
            self.map_to_neo4j(user, 'Played_Track', user_played_tracks, "played")
        )
        logger.debug("User likes saved successfully")
