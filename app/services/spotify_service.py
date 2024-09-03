import os
import spotipy
from asgiref.sync import sync_to_async
from typing import List, Tuple
import asyncio
import logging
import aiohttp
from neomodel import db
from neomodel.async_.core import AsyncDatabase
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack
from app.db_models.spotify.spotify_album import SpotifyAlbum
from app.db_models.spotify.spotify_genre import SpotifyGenre
from app.db_models.spotify.spotify_image import SpotifyImage
from app.db_models.node_resolver import resolve_node_class
from app.db_models.liked_item import LikedItem  # Ensure LikedItem is imported
from app.services.service_strategy import ServiceStrategy
from spotipy.oauth2 import SpotifyOAuth
from app.db_models.spotify.spotify_user import SpotifyUser
from neomodel.exceptions import NodeClassAlreadyDefined
import traceback
from app.db_models.user import User  # Add this line
import neomodel

logger = logging.getLogger('app')

def get_async_db():
    return AsyncDatabase()


class SpotifyService(ServiceStrategy):
    def __init__(self, client_id, client_secret, redirect_uri):
        super().__init__()
        logger.debug('Initializing SpotifyService with client_id=%s', client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = 'user-library-read user-library-modify user-top-read user-follow-read user-read-recently-played'
        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        self.spotify_client = None
        logger.info('SpotifyService initialized successfully.')

    async def create_authorize_url(self) -> str:
        logger.debug('Creating authorize URL')
        return self.auth_manager.get_authorize_url()

    async def get_tokens(self, code):
        logger.debug('Getting tokens for code=%s', code)
        tokens = await sync_to_async(self.auth_manager.get_access_token)(code=code, check_cache=False)
        logger.info('Tokens retrieved successfully')
        return tokens

    async def refresh_access_token(self, refresh_token):
        logger.debug('Refreshing access token for refresh_token=%s', refresh_token)
        tokens = await sync_to_async(self.auth_manager.refresh_access_token)(refresh_token)
        logger.info('Access token refreshed successfully')
        return tokens

    async def get_user_profile(self, tokens):
        logger.debug('Getting user profile with access_token')
        sp = spotipy.Spotify(auth=tokens['access_token'])
        user_profile = await sync_to_async(sp.current_user)()
        logger.info('User profile retrieved successfully')
        return user_profile

    async def initialize_client(self, user):
        token_info = self.auth_manager.get_cached_token()
        if not token_info:
            # Handle the case where there's no token (e.g., redirect to auth)
            return False
        self.spotify_client = spotipy.Spotify(auth_manager=self.auth_manager)
        return True

    async def fetch_top_artists(self, user, limit=50):
        logger.debug('Fetching top artists for user=%s with limit=%d', user, limit)
        return await self.fetch_with_retries(self._fetch_top_artists, user, limit)

    async def fetch_top_tracks(self, user, limit=50):
        logger.debug('Fetching top tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_with_retries(self._fetch_top_tracks, user, limit)

    async def fetch_saved_tracks(self, user, limit=50):
        logger.debug('Fetching saved tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_with_retries(self._fetch_saved_tracks, user, limit)

    async def fetch_saved_albums(self, user, limit=50):
        logger.debug('Fetching saved albums for user=%s with limit=%d', user, limit)
        return await self.fetch_with_retries(self._fetch_saved_albums, user, limit)

    async def fetch_followed_artists(self, user, limit=50):
        logger.debug('Fetching followed artists for user=%s with limit=%d', user, limit)
        sp = spotipy.Spotify(auth=user.access_token)
        all_artists = []
        after = None
        
        while len(all_artists) < limit:
            response = await sync_to_async(sp.current_user_followed_artists)(limit=limit, after=after)
            artists = response['artists']['items']
            all_artists.extend(artists)
            
            if len(all_artists) >= limit or not response['artists']['next']:
                all_artists = all_artists[:limit]
                break
            
            # Update 'after' parameter with the last artist's ID
            after = artists[-1]['id']
        
        logger.info('Followed artists retrieved successfully')
        return all_artists

    async def fetch_user_playlists(self, user, limit=50):
        logger.debug('Fetching user playlists for user=%s with limit=%d', user, limit)
        sp = spotipy.Spotify(auth=user.access_token)
        offset = 0
        all_playlists = []
        while True:
            response = await sync_to_async(sp.current_user_playlists)(limit=limit, offset=offset)
            all_playlists.extend(response['items'])
            if len(response['items']) < limit:
                break
            offset += limit
        logger.info('User playlists retrieved successfully')
        return all_playlists

    async def fetch_top_genres(self, user, limit=50):
        logger.debug('Fetching top genres for user=%s with limit=%d', user, limit)
        top_artists = await self.fetch_top_artists(user, limit)
        genre_count = {}
        for artist in top_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        logger.info('Top genres retrieved successfully')
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    async def fetch_liked_genres(self, spotify_user):
        try:
            # Create a Spotify client using the user's access token
            sp = spotipy.Spotify(auth=spotify_user.access_token)
            
            # Fetch top artists and tracks
            top_artists = await sync_to_async(sp.current_user_top_artists)(limit=50, time_range='medium_term')
            top_tracks = await sync_to_async(sp.current_user_top_tracks)(limit=50, time_range='medium_term')
            
            genres = set()
            for artist in top_artists['items']:
                genres.update(artist.get('genres', []))
            
            # For tracks, we need to fetch the artist information to get genres
            for track in top_tracks['items']:
                artist_id = track['artists'][0]['id']
                artist = await sync_to_async(sp.artist)(artist_id)
                genres.update(artist.get('genres', []))
            
            logger.debug(f"Fetched liked genres: {len(genres)}")
            return list(genres)
        except Exception as e:
            logger.error(f"Error fetching liked genres: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def fetch_recently_played(self, user, limit=50):
        logger.debug('Fetching recently played tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_with_retries(self._fetch_recently_played, user, limit)

    async def fetch_with_retries(self, func, *args, max_retries=5, backoff_factor=1):
        """
        Fetch data with retry logic and exponential backoff.
        
        :param func: The function to call.
        :param args: Arguments to pass to the function.
        :param max_retries: Maximum number of retry attempts.
        :param backoff_factor: Factor by which to increase the wait time between retries.
        :return: Result of the function call.
        """
        for attempt in range(max_retries):
            try:
                return await func(*args)
            except Exception as e:
                if hasattr(e, 'http_status') and e.http_status == 429:  # Rate limit error
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"An error occurred: {e}")
                    raise
        raise Exception("Max retries exceeded.")

    async def _fetch_top_artists(self, user, limit):
        sp = spotipy.Spotify(auth=user.access_token)
        offset = 0
        all_artists = []
        while True:
            response = await sync_to_async(sp.current_user_top_artists)(limit=limit, offset=offset, time_range='short_term')
            all_artists.extend(response['items'])
            if len(response['items']) < limit:
                break
            offset += limit
        return all_artists

    async def _fetch_top_tracks(self, user, limit):
        sp = spotipy.Spotify(auth=user.access_token)
        offset = 0
        all_tracks = []
        while True:
            response = await sync_to_async(sp.current_user_top_tracks)(limit=limit, offset=offset, time_range='short_term')
            all_tracks.extend(response['items'])
            if len(response['items']) < limit:
                break
            offset += limit
        return all_tracks

    async def _fetch_saved_tracks(self, user, limit):
        sp = spotipy.Spotify(auth=user.access_token)
        offset = 0
        all_tracks = []
        while True:
            response = await sync_to_async(sp.current_user_saved_tracks)(limit=limit, offset=offset)
            all_tracks.extend([item['track'] for item in response['items']])
            if len(response['items']) < limit:
                break
            offset += limit
        return all_tracks

    async def _fetch_saved_albums(self, user, limit):
        sp = spotipy.Spotify(auth=user.access_token)
        offset = 0
        all_albums = []
        while True:
            response = await sync_to_async(sp.current_user_saved_albums)(limit=limit, offset=offset)
            all_albums.extend([item['album'] for item in response['items']])
            if len(response['items']) < limit:
                break
            offset += limit
        return all_albums

    async def _fetch_recently_played(self, user, limit):
        sp = spotipy.Spotify(auth=user.access_token)
        after = None
        before = None
        all_tracks = []
        while True:
            response = await sync_to_async(sp.current_user_recently_played)(limit=limit, after=after, before=before)
            all_tracks.extend([item['track'] for item in response['items']])
            if len(response['items']) < limit:
                break
            # Adjust 'after' or 'before' for pagination if necessary
            after = response['items'][-1]['played_at'] if response['items'] else None
        return all_tracks

    @staticmethod
    async def create_or_update_image(image_data):
        try:
            if not image_data or 'url' not in image_data:
                logger.warning(f"Invalid image data: {image_data}")
                return None

            properties = {
                'height': image_data.get('height'),
                'width': image_data.get('width'),
                'url': image_data['url'],
            }

            try:
                image = await SpotifyImage.nodes.get(url=image_data['url'])
                # Update existing image
                for key, value in properties.items():
                    setattr(image, key, value)
                await image.save()
            except SpotifyImage.DoesNotExist:
                # Create new image
                image = SpotifyImage(**properties)
                await image.save()
            except neomodel.exceptions.MultipleNodesReturned:
                # Handle multiple nodes
                images = await SpotifyImage.nodes.filter(url=image_data['url'])
                image = images[0]  # Use the first image found
                # Update the first image
                for key, value in properties.items():
                    setattr(image, key, value)
                await image.save()
                # Delete the duplicates
                for duplicate in images[1:]:
                    await duplicate.delete()
                logger.warning(f"Found and cleaned up duplicate images for URL: {image_data['url']}")

            return image
        except Exception as e:
            logger.error(f"Error creating/updating image: {str(e)}")
            logger.error(f"Image data: {image_data}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def process_track(track_data):
        try:
            properties = {
                'spotify_id': track_data['id'],
                'name': track_data['name'],
                'uri': track_data['uri'],
                'duration_ms': track_data['duration_ms'],
                'spotify_url': track_data['external_urls']['spotify'],
                'href': track_data.get('href', ''),
                'popularity': track_data.get('popularity', 0),
                'type': track_data.get('type', 'track'),
                'disc_number': track_data.get('disc_number', 1),
                'explicit': track_data.get('explicit', False),
                'isrc': track_data.get('external_ids', {}).get('isrc', ''),
                'preview_url': track_data.get('preview_url', ''),
                'track_number': track_data.get('track_number', 0),
            }

            # Fetch all nodes with the given spotify_id
            query = """
            MATCH (n)
            WHERE n.spotify_id = $spotify_id
            RETURN n, labels(n) as labels
            """
            adb = get_async_db()
            results, _ = await adb.cypher_query(query, {'spotify_id': track_data['id']})

            tracks = []
            for result in results:
                node = result[0]
                labels = result[1]
                node_class = resolve_node_class(labels) or SpotifyTrack
                if node_class:
                    tracks.append(node_class.inflate(node))

            if len(tracks) > 1:
                # If multiple nodes found, keep the first one and delete the rest
                logger.warning(f"Found {len(tracks)} tracks with spotify_id {track_data['id']}. Cleaning up duplicates.")
                track = tracks[0]
                for duplicate in tracks[1:]:
                    await duplicate.delete()
            elif len(tracks) == 1:
                track = tracks[0]
            else:
                track = None

            if track:
                # Update existing track
                for key, value in properties.items():
                    setattr(track, key, value)
                await track.save()
            else:
                # Create new track
                track = SpotifyTrack(**properties)
                await track.save()

            # Process and connect images
            for image_data in track_data.get('album', {}).get('images', []):
                image = await SpotifyService.create_or_update_image(image_data)
                if image:
                    await track.images.connect(image)

            return track
        except Exception as e:
            logger.error(f"Error processing track: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def process_artist(artist_data):
        try:
            properties = {
                'spotify_id': artist_data['id'],
                'name': artist_data['name'],
                'uri': artist_data.get('uri', ''),
                'spotify_url': artist_data.get('external_urls', {}).get('spotify', ''),
                'href': artist_data.get('href', ''),
                'popularity': artist_data.get('popularity', 0),
                'followers': artist_data.get('followers', {}).get('total', 0),
            }

            try:
                artist = await SpotifyArtist.nodes.get(spotify_id=artist_data['id'])
                # Update existing artist
                for key, value in properties.items():
                    setattr(artist, key, value)
                await artist.save()
            except SpotifyArtist.DoesNotExist:
                # Create new artist
                artist = SpotifyArtist(**properties)
                await artist.save()
            except neomodel.exceptions.MultipleNodesReturned:
                # Handle multiple nodes
                artists = await SpotifyArtist.nodes.filter(spotify_id=artist_data['id'])
                artist = artists[0]  # Use the first artist found
                # Update the first artist
                for key, value in properties.items():
                    setattr(artist, key, value)
                await artist.save()
                # Delete the duplicates
                for duplicate in artists[1:]:
                    await duplicate.delete()
                logger.warning(f"Found and cleaned up duplicate artists for spotify_id: {artist_data['id']}")

            # Process and connect images
            for image_data in artist_data.get('images', []):
                image = await SpotifyService.create_or_update_image(image_data)
                if image:
                    await artist.images.connect(image)

            return artist
        except Exception as e:
            logger.error(f"Error processing artist: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def process_album(album_data):
        try:
            properties = {
                'spotify_id': album_data['id'],
                'name': album_data['name'],  # Ensure this is included
                'uri': album_data.get('uri', ''),
                'spotify_url': album_data.get('external_urls', {}).get('spotify', ''),
                'href': album_data.get('href', ''),
                'album_type': album_data.get('album_type', ''),
                'release_date': album_data.get('release_date', ''),
                'release_date_precision': album_data.get('release_date_precision', ''),
                'total_tracks': album_data.get('total_tracks', 0),
            }

            try:
                album = await SpotifyAlbum.nodes.get(spotify_id=album_data['id'])
                # Update existing album
                for key, value in properties.items():
                    setattr(album, key, value)
                await album.save()
            except SpotifyAlbum.DoesNotExist:
                # Create new album
                album = SpotifyAlbum(**properties)
                await album.save()
            except neomodel.exceptions.MultipleNodesReturned:
                # Handle multiple nodes
                albums = await SpotifyAlbum.nodes.filter(spotify_id=album_data['id'])
                album = albums[0]  # Use the first album found
                # Update the first album
                for key, value in properties.items():
                    setattr(album, key, value)
                await album.save()
                # Delete the duplicates
                for duplicate in albums[1:]:
                    await duplicate.delete()
                logger.warning(f"Found and cleaned up duplicate albums for spotify_id: {album_data['id']}")

            # Process and connect images
            for image_data in album_data.get('images', []):
                image = await SpotifyService.create_or_update_image(image_data)
                if image:
                    await album.images.connect(image)

            return album
        except Exception as e:
            logger.error(f"Error processing album: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def process_genre(genre_data):
        try:
            if isinstance(genre_data, str):
                genre_name = genre_data
            elif isinstance(genre_data, tuple):
                genre_name = genre_data[0]  # Extract just the name
            elif isinstance(genre_data, dict):
                genre_name = genre_data.get('name')
            else:
                logger.error(f"Unexpected genre data type: {type(genre_data)}")
                return None

            if not genre_name:
                logger.error(f"Invalid genre data: {genre_data}")
                return None

            try:
                # Use a Cypher query to get or create the genre
                query = """
                MERGE (g:SpotifyGenre {name: $name})
                ON CREATE SET g.uid = randomUUID()
                RETURN g
                """
                results, _ = db.cypher_query(query, {'name': genre_name})
                genre = SpotifyGenre.inflate(results[0][0])
                return genre
            except Exception as e:
                logger.error(f"Error creating or retrieving genre: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error args: {e.args}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None

        except Exception as e:
            logger.error(f"Error processing Genre: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def map_to_neo4j(spotify_user, label, items, relation_type):
        logger.debug(f"Mapping {len(items)} {label}s to Neo4j for user {spotify_user.username} with relation type {relation_type}")
        for item in items:
            try:
                if label == 'Track':
                    node = await SpotifyService.process_track(item)
                elif label == 'Artist':
                    node = await SpotifyService.process_artist(item)
                elif label == 'Album':
                    node = await SpotifyService.process_album(item)
                elif label == 'Genre':
                    node = SpotifyService.process_genre(item)  # Note: This is now synchronous
                else:
                    logger.error(f"Unsupported label: {label}")
                    continue

                if node:
                    relationship_attr = {
                        'TOP_ARTIST': 'top_artists',
                        'TOP_TRACK': 'top_tracks',
                        'TOP_GENRE': 'top_genres',
                        'LIKES_ARTIST': 'likes_artists',
                        'LIKES_TRACK': 'likes_tracks',
                        'LIKES_GENRE': 'likes_genres',
                        'LIKES_ALBUM': 'likes_albums',
                        'PLAYED_TRACK': 'played_tracks',
                        'SAVED_ALBUM': 'saved_albums'
                    }.get(relation_type)

                    if relationship_attr:
                        await getattr(spotify_user, relationship_attr).connect(node)
                        logger.debug(f"Created relationship {relation_type} between {spotify_user.username} and {node}")
                    else:
                        logger.error(f"Unsupported relation type: {relation_type}")
                else:
                    logger.error(f"Failed to create or retrieve node for {label}: {item}")
            except Exception as e:
                logger.error(f"Error processing {label}: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error args: {e.args}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Item data: {item}")  # Add this line to log the item data
        logger.debug(f"Finished mapping {len(items)} {label}s to Neo4j for user {spotify_user.username}")

    @staticmethod
    async def create_relationship(user, node, label, relation_type):
        try:
            user_node = await SpotifyUser.nodes.get(spotify_id=user.spotify_id)
            if node is None:
                logger.error(f"Cannot create relationship: node is None for {label}")
                return

            if label == 'Track':
                if relation_type == "top":
                    await user_node.top_tracks.connect(node)
                elif relation_type == "saved":
                    await user_node.saved_tracks.connect(node)
            elif label == 'Artist':
                if relation_type == "top":
                    await user_node.top_artists.connect(node)
                elif relation_type == "followed":
                    await user_node.likes_artists.connect(node)
            elif label == 'Album':
                await user_node.saved_albums.connect(node)
            elif label == 'Genre':
                if not isinstance(node, SpotifyGenre):
                    logger.error(f"Expected node of class SpotifyGenre, got {type(node)}")
                    return
                if relation_type == "top":
                    await user_node.top_genres.connect(node)
                elif relation_type == "liked":
                    await user_node.likes_genres.connect(node)
            logger.info(f'Connected user {user.spotify_id} with {relation_type} {label} {node.name}')
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    def get_node_class(self, label):
        if label == 'Track':
            return SpotifyTrack
        elif label == 'Artist':
            return SpotifyArtist
        elif label == 'Album':
            return SpotifyAlbum
        elif label == 'Genre':
            return SpotifyGenre
        else:
            return None
        
    async def get_spotify_user(self, parent_user):
        spotify_accounts = await parent_user.spotify_account.all()
        if not spotify_accounts:
            raise ValueError(f"No Spotify account found for user {parent_user.uid}")
        return spotify_accounts[0]  # Assuming one Spotify account per user

    async def get_user_likes(self, parent_user):
        spotify_user = await self.get_spotify_user(parent_user)
        # Implement this method to fetch user likes from Spotify
        # Return the likes in the format expected by save_user_likes
        pass

    async def save_user_likes(self, parent_user, user_likes=None):
        try:
            spotify_user = await self.get_spotify_user(parent_user)
            logger.debug(f"Saving user likes for Spotify user: {spotify_user.username}")
            if spotify_user.username is None:
                logger.error(f"Spotify user has no username. User object: {spotify_user}")

            # Clear existing user likes
            await self.clear_user_likes(spotify_user)
            
            if user_likes is None:
                # Fetch all types of user data
                top_artists = await self.fetch_top_artists(spotify_user)
                top_tracks = await self.fetch_top_tracks(spotify_user)
                top_genres = await self.fetch_top_genres(spotify_user)
                saved_tracks = await self.fetch_saved_tracks(spotify_user)
                saved_albums = await self.fetch_saved_albums(spotify_user)
                followed_artists = await self.fetch_followed_artists(spotify_user)
                recently_played = await self.fetch_recently_played(spotify_user)
                liked_genres = await self.fetch_liked_genres(spotify_user)
                
                logger.debug(f"Fetched top artists: {len(top_artists)}")
                logger.debug(f"Fetched top tracks: {len(top_tracks)}")
                logger.debug(f"Fetched top genres: {len(top_genres)}")
                logger.debug(f"Fetched saved tracks: {len(saved_tracks)}")
                logger.debug(f"Fetched saved albums: {len(saved_albums)}")
                logger.debug(f"Fetched followed artists: {len(followed_artists)}")
                logger.debug(f"Fetched recently played: {len(recently_played)}")
                logger.debug(f"Fetched liked genres: {len(liked_genres)}")
                
                # Map data to Neo4j
                await asyncio.gather(
                    self.map_to_neo4j(spotify_user, 'Artist', top_artists, "TOP_ARTIST"),
                    self.map_to_neo4j(spotify_user, 'Track', top_tracks, "TOP_TRACK"),
                    self.map_to_neo4j(spotify_user, 'Genre', top_genres, "TOP_GENRE"),
                    self.map_to_neo4j(spotify_user, 'Track', saved_tracks, "LIKES_TRACK"),
                    self.map_to_neo4j(spotify_user, 'Album', saved_albums, "SAVED_ALBUM"),
                    self.map_to_neo4j(spotify_user, 'Artist', followed_artists, "LIKES_ARTIST"),
                    self.map_to_neo4j(spotify_user, 'Track', recently_played, "PLAYED_TRACK"),
                    self.map_to_neo4j(spotify_user, 'Genre', liked_genres, "LIKES_GENRE")
                )
            else:
                # Process the provided user_likes
                for like in user_likes:
                    if not isinstance(like, dict):
                        logger.error("Each item in 'user_likes' must be a dictionary")
                        continue

                    try:
                        await self.process_like(spotify_user, like)
                    except Exception as e:
                        logger.error(f"Error processing like: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        logger.error(f"Error args: {e.args}")
                        logger.error(f"Traceback: {traceback.format_exc()}")

            logger.debug("User likes saved successfully")
        except Exception as e:
            logger.error(f"Error in save_user_likes: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def process_like(self, spotify_user, like):
        node_labels = like.get('labels', [])
        logger.debug(f"Processing like with labels: {node_labels}")
        
        resolved_class = resolve_node_class(node_labels)
        if resolved_class is None:
            logger.error(f"Node with labels {node_labels} does not resolve to any of the known objects")
            return

        spotify_id = like.get('spotify_id')
        if not spotify_id:
            logger.error("No spotify_id found in like data")
            return

        # Get or create the node
        node = await resolved_class.nodes.get_or_none(spotify_id=spotify_id)
        if node is None:
            # Create a new node with only the properties defined in the model
            node_properties = {
                'spotify_id': spotify_id,
                'name': like.get('name'),
                'uid': like.get('uid')
            }
            # Add other properties that are defined in your model
            node = resolved_class(**node_properties)
            await node.save()

        # Add the relationship to the user based on the resolved class
        if issubclass(resolved_class, SpotifyArtist):
            await spotify_user.likes_artists.connect(node)
        elif issubclass(resolved_class, SpotifyTrack):
            await spotify_user.likes_tracks.connect(node)
        elif issubclass(resolved_class, SpotifyAlbum):
            await spotify_user.likes_albums.connect(node)
        elif issubclass(resolved_class, SpotifyGenre):
            await spotify_user.likes_genres.connect(node)
        else:
            logger.warning(f"Unhandled class type: {resolved_class}")

    async def clear_user_likes(self, spotify_user):
        logger.debug(f"Clearing user likes for Spotify user: {spotify_user.username}")

        # Disconnect existing relationships
        await asyncio.gather(
            spotify_user.top_artists.disconnect_all(),
            spotify_user.top_tracks.disconnect_all(),
            spotify_user.top_genres.disconnect_all(),
            spotify_user.likes_artists.disconnect_all(),
            spotify_user.likes_tracks.disconnect_all(),
            spotify_user.likes_genres.disconnect_all(),
            spotify_user.likes_albums.disconnect_all(),
            spotify_user.played_tracks.disconnect_all(),
            spotify_user.saved_tracks.disconnect_all(),
            spotify_user.saved_albums.disconnect_all()
        )
        logger.debug("User likes cleared successfully")

