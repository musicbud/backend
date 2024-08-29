import spotipy
from spotipy.oauth2 import SpotifyOAuth
from asgiref.sync import sync_to_async
from typing import List, Tuple
import asyncio
import logging

from app.services.service_strategy import ServiceStrategy
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack
from app.db_models.spotify.spotify_genre import SpotifyGenre
from app.db_models.spotify.spotify_album import SpotifyAlbum

logger = logging.getLogger('app')

class SpotifyService(ServiceStrategy):
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        logger.debug('Initializing SpotifyService with client_id=%s', client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.auth_manager = SpotifyOAuth(client_id=self.client_id,
                                         client_secret=self.client_secret,
                                         redirect_uri=self.redirect_uri,
                                         scope=self.scope)
        logger.info('SpotifyService initialized successfully.')

    async def create_authorize_url(self):
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

    async def fetch_liked_genres(self, user, limit=50):
        logger.debug('Fetching liked genres for user=%s with limit=%d', user, limit)
        liked_tracks = await self.fetch_followed_artists(user, limit)
        genre_count = {}
        for track in liked_tracks:
            for genre in track.get('genres', []):
                genre_count[genre] = genre_count.get(genre, 0) + 1
        logger.info('Liked genres retrieved successfully')
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    
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

    async def map_to_neo4j(self, user, label, items, relation_type="top"):
        logger.debug('Mapping items to Neo4j for user=%s, label=%s, relation_type=%s', user, label, relation_type)

        for item in items:
            node = None

            if label == 'Artist':
                artist_data = item
                logger.debug('Processing Artist: %s', artist_data['name'])
                node = await SpotifyArtist.nodes.get_or_none(spotify_id=artist_data['id'])
                if not node:
                    logger.debug('Creating new Spotify Artist node: %s', artist_data['name'])
                    node = await SpotifyArtist(
                        spotify_id=artist_data['id'],
                        name=artist_data['name'],
                        uri=artist_data['uri'],
                        genres=artist_data['genres'],
                        spotify_url=artist_data['external_urls']['spotify']
                    ).save()
                if relation_type == "top":
                    await user.top_artists.connect(node)
                    await user.likes_artists.connect(node)
                    logger.info('Connected user %s with Top Artist %s', user, artist_data['name'])
                if relation_type == "liked":
                    await user.likes_artists.connect(node)
                    logger.info('Connected user %s with Liked Artist %s', user, artist_data['name'])

            elif label == 'Track':
                track_data = item
                logger.debug('Processing Track: %s', track_data['name'])
                node = await SpotifyTrack.nodes.get_or_none(spotify_id=track_data['id'])
                if not node:
                    logger.debug('Creating new Track node: %s', track_data['name'])
                    node = await SpotifyTrack(
                        spotify_id=track_data['id'],
                        name=track_data['name'],
                        uri=track_data['uri'],
                        duration_ms=track_data['duration_ms'],
                        spotify_url=track_data['external_urls']['spotify']
                    ).save()
                if relation_type == "top":
                    await user.top_tracks.connect(node)
                    await user.likes_tracks.connect(node)
                    logger.info('Connected user %s with Top Track %s', user, track_data['name'])
                elif relation_type == "saved":
                    await user.saved_tracks.connect(node)
                    logger.info('Connected user %s with Saved Track %s', user, track_data['name'])
                elif relation_type == "recently_played":
                    await user.played_tracks.connect(node)
                    logger.info('Connected user %s with Recently Played Track %s', user, track_data['name'])

            elif label == 'Album':
                album_data = item
                logger.debug('Processing Album: %s', album_data['name'])
                node = await SpotifyAlbum.nodes.get_or_none(spotify_id=album_data['id'])
                if not node:
                    logger.debug('Creating new Album node: %s', album_data['name'])
                    node = await SpotifyAlbum(
                        spotify_id=album_data['id'],
                        name=album_data['name'],
                        uri=album_data['uri'],
                        release_date=album_data['release_date'],
                        spotify_url=album_data['external_urls']['spotify']
                    ).save()
                if relation_type == "top":
                    await user.likes_albums.connect(node)
                    logger.info('Connected user %s with Top Album %s', user, album_data['name'])
                elif relation_type == "saved":
                    await user.saved_albums.connect(node)
                    logger.info('Connected user %s with Saved Album %s', user, album_data['name'])

            elif label == 'Genre':
                genre_data = item[0]
                logger.debug('Processing Genre: %s', genre_data)
                node = await SpotifyGenre.nodes.get_or_none(name=genre_data)
                if not node:
                    logger.debug('Creating new Genre node: %s', genre_data)
                    node = await SpotifyGenre(name=genre_data).save()
                if relation_type == "top":
                    await user.top_genres.connect(node)
                    logger.info('Connected user %s with Top Genre %s', user, genre_data)
                elif relation_type == "liked":
                    await user.likes_genres.connect(node)
                    logger.info('Connected user %s with Liked Genre %s', user, genre_data)

    async def save_user_likes(self, user):
        logger.debug('Saving user likes for user=%s', user)

        try:
            # Fetch and map top artists
            top_artists = await self.fetch_top_artists(user)
            await self.map_to_neo4j(user, 'Artist', top_artists, relation_type="top")
            logger.info('Saved top artists successfully for user=%s', user)

            # Fetch and map top tracks
            top_tracks = await self.fetch_top_tracks(user)
            await self.map_to_neo4j(user, 'Track', top_tracks, relation_type="top")
            logger.info('Saved top tracks successfully for user=%s', user)

            # Fetch and map saved tracks
            saved_tracks = await self.fetch_saved_tracks(user)
            await self.map_to_neo4j(user, 'Track', saved_tracks, relation_type="saved")
            logger.info('Saved tracks successfully for user=%s', user)

            # Fetch and map saved albums
            saved_albums = await self.fetch_saved_albums(user)
            await self.map_to_neo4j(user, 'Album', saved_albums, relation_type="saved")
            logger.info('Saved albums successfully for user=%s', user)

            # Fetch and map followed artists
            followed_artists = await self.fetch_followed_artists(user)
            await self.map_to_neo4j(user, 'Artist', followed_artists, relation_type="liked")
            logger.info('Saved followed artists successfully for user=%s', user)

            # Fetch and map user playlists (You may want to map playlists separately)
            user_playlists = await self.fetch_user_playlists(user)
            logger.info('Fetched user playlists successfully for user=%s', user)

            # Fetch and map top genres
            top_genres = await self.fetch_top_genres(user)
            await self.map_to_neo4j(user, 'Genre', top_genres, relation_type="top")
            logger.info('Saved top genres successfully for user=%s', user)

            # Fetch and map liked genres
            liked_genres = await self.fetch_liked_genres(user)
            await self.map_to_neo4j(user, 'Genre', liked_genres, relation_type="liked")
            logger.info('Saved liked genres successfully for user=%s', user)

            # Fetch and map recently played tracks
            recently_played = await self.fetch_recently_played(user)
            await self.map_to_neo4j(user, 'Track', recently_played, relation_type="recently_played")
            logger.info('Saved recently played tracks successfully for user=%s', user)

        except Exception as e:
            logger.error(f"Error saving user likes for user: {user.id} - {e}")
            raise

        logger.info('Saving user likes completed')

    async def clear_user_likes(self, user):
        logger.debug('Clearing user likes for user=%s', user)
        
        # Clear liked artists
        liked_artists = await user.likes_artists.all()
        for artist in liked_artists:
            await user.likes_artists.disconnect(artist)
            logger.info('Disconnected user %s from Artist %s', user, artist.name)
        
        # Clear liked tracks
        liked_tracks = await user.likes_tracks.all()
        for track in liked_tracks:
            await user.likes_tracks.disconnect(track)
            logger.info('Disconnected user %s from Track %s', user, track.name)
        
        # Clear liked albums
        liked_albums = await user.likes_albums.all()
        for album in liked_albums:
            await user.likes_albums.disconnect(album)
            logger.info('Disconnected user %s from Album %s', user, album.name)
        
        # Clear liked genres
        liked_genres = await user.likes_genres.all()
        for genre in liked_genres:
            await user.likes_genres.disconnect(genre)
            logger.info('Disconnected user %s from Genre %s', user, genre.name)
        
        logger.info('Clearing user likes completed')

    async def sync_user_to_neo4j(self, user):
        logger.info(f"Syncing user {user.username} to Neo4j")
        try:
            await self.save_user_likes(user)
            logger.info(f"Successfully synced user {user.username} to Neo4j")
        except Exception as e:
            logger.error(f"Error syncing user {user.username} to Neo4j: {e}")
            raise
