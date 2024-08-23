import time 
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from asgiref.sync import sync_to_async
from typing import List, Tuple

from .service_strategy import ServiceStrategy
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack
from app.db_models.spotify.spotify_genre import SpotifyGenre
from app.db_models.spotify.spotify_album import SpotifyAlbum

from django.http import JsonResponse

import asyncio
from asgiref.sync import sync_to_async

import logging

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
        return await self.fetch_all_items(user, 'top_artists', limit)

    async def fetch_top_tracks(self, user, limit=50):
        logger.debug('Fetching top tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_all_items(user, 'top_tracks', limit)

    async def fetch_followed_artists(self, user, limit=50):
        logger.debug('Fetching followed artists for user=%s with limit=%d', user, limit)
        return await self.fetch_all_items(user, 'followed_artists', limit)

    async def fetch_saved_tracks(self, user, limit=50):
        logger.debug('Fetching saved tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_all_items(user, 'saved_tracks', limit)

    async def fetch_saved_albums(self, user, limit=50):
        logger.debug('Fetching saved albums for user=%s with limit=%d', user, limit)
        return await self.fetch_all_items(user, 'saved_albums', limit)

    async def fetch_top_genres(self, user, limit=50):
        logger.debug('Fetching top genres for user=%s with limit=%d', user, limit)
        top_artists = await self.fetch_top_artists(user, limit)
        genre_count = {}
        for artist in top_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        logger.info('Top genres retrieved successfully')
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    async def fetch_followed_genres(self, user, limit=50):
        logger.debug('Fetching followed genres for user=%s with limit=%d', user, limit)
        followed_artists = await self.fetch_followed_artists(user, limit)
        genre_count = {}
        for artist in followed_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        logger.info('Followed genres retrieved successfully')
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    async def fetch_recently_played(self, user, limit=50):
        logger.debug('Fetching recently played tracks for user=%s with limit=%d', user, limit)
        return await self.fetch_all_items(user, 'recently_played', limit)

    
    async def fetch_all_items(self, user, item_type, limit=50):
        logger.debug('Fetching all items of type=%s for user=%s with limit=%d', item_type, user, limit)
        sp = spotipy.Spotify(auth=user.access_token)
        items = []
        offset = 0
        after = None
        before = None
        
        while True:
            if item_type == 'top_artists':
                response = await sync_to_async(sp.current_user_top_artists)(limit=limit, offset=offset, time_range='long_term')
                items.extend(response['items'])
                if len(response['items']) < limit:
                    break
                offset += limit
            elif item_type == 'top_tracks':
                response = await sync_to_async(sp.current_user_top_tracks)(limit=limit, offset=offset, time_range='long_term')
                items.extend(response['items'])
                if len(response['items']) < limit:
                    break
                offset += limit
            elif item_type == 'followed_artists':
                response = await sync_to_async(sp.current_user_followed_artists)(limit=limit, after=after)
                items.extend(response['artists']['items'])
                if len(response['artists']['items']) < limit:
                    break
                after = response['artists']['cursors']['after']
            elif item_type == 'saved_tracks':
                response = await sync_to_async(sp.current_user_saved_tracks)(limit=limit, offset=offset)
                items.extend([item['track'] for item in response['items']])
                if len(response['items']) < limit:
                    break
                offset += limit
            elif item_type == 'saved_albums':
                response = await sync_to_async(sp.current_user_saved_albums)(limit=limit, offset=offset)
                items.extend([item['album'] for item in response['items']])
                if len(response['items']) < limit:
                    break
                offset += limit
            elif item_type == 'recently_played':
                response = await sync_to_async(sp.current_user_recently_played)(limit=limit, after=after, before=before)
                items.extend([item['track'] for item in response['items']])
                if len(response['items']) < limit:
                    break
                after = response['items'][-1]['played_at']
            else:
                logger.error('Invalid item_type: %s', item_type)
                raise ValueError("Invalid item_type.")
        
        logger.info('Items of type=%s fetched successfully for user=%s', item_type, user)
        return items
    

    async def fetch_with_retries(func, *args, max_retries=5, backoff_factor=1):
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
                    time.sleep(wait_time)
                else:
                    logger.error(f"An error occurred: {e}")
                    raise
        raise Exception("Max retries exceeded.")

    async def map_to_neo4j(self, user, label, items, relation_type="top"):
        logger.debug('Mapping items to Neo4j for user=%s, label=%s, relation_type=%s', user, label, relation_type)

        for item in items:
            node = None

            if label == 'Artist':
                artist_data = item
                logger.debug('Processing Artist: %s', artist_data['name'])
                node = await SpotifyArtist.nodes.get_or_none(spotify_id=artist_data['id'])
                if not node:
                    logger.debug('Creating new Artist node: %s', artist_data['name'])
                    node = await SpotifyArtist(
                        spotify_id=artist_data['id'],
                        name=artist_data['name'],
                        uri=artist_data['uri'],
                        spotify_url=artist_data['external_urls']['spotify'],
                        followers=artist_data['followers']['total'],
                        href= artist_data['href'],
                        images= [image['url'] for image in artist_data['images']],
                        image_heights =[image['height'] for image in artist_data['images']],
                        image_widthes = [image['width'] for image in artist_data['images']],
                        genres= artist_data['genres']
                    ).save()
                if relation_type == "top":
                    logger.info(f"user {type (user)}")
                    logger.info(f"user {user}")

                    logger.info(f"node  {type (node)}")
                    logger.info(f"node {node}")
                    
                    logger.info(f"likes rel  {type(user.top_artists)}")

                    await user.top_artists.connect(node)
                    logger.info(f"user.likes_artists {user.top_artists}")
                    await user.likes_artists.connect(node)
                elif relation_type == "followed":
                    await user.likes_artists.connect(node)
                logger.debug('Artist processed: %s', artist_data['name'])

            elif label == 'Track':
                track_data = item
                logger.debug('Processing Track: %s', track_data['name'])
                node = await SpotifyTrack.nodes.get_or_none(spotify_id=track_data['id'])
                if not node:
                    logger.debug('Creating new Track node: %s', track_data['name'])
                    node = await SpotifyTrack(
                        spotify_id=track_data['id'],
                        name=track_data['name'],
                        href= track_data['href'],
                        duration_ms=track_data['duration_ms'],
                        disc_number=track_data['disc_number'],
                        explicit=track_data['explicit'],
                        isrc=track_data['external_ids']['isrc'],
                        popularity=track_data['popularity'],
                        preview_url=track_data['preview_url'],
                        track_number=track_data['track_number'],
                        uri=track_data['uri'],
                        spotify_url=track_data['external_urls']['spotify'],
                    ).save()
                if relation_type == "top":
                    await user.top_tracks.connect(node)
                    await user.likes_tracks.connect(node)
                elif relation_type == "saved":
                    await user.likes_tracks.connect(node)
                elif relation_type == "played":
                    await user.played_tracks.connect(node)
                logger.debug('Track processed: %s', track_data['name'])

                # Link track to album
                album_data = track_data['album']
                album_node = await SpotifyAlbum.nodes.get_or_none(spotify_id=album_data['id'])
                if not album_node:
                    logger.debug('Creating new Album node: %s', album_data['name'])
                    album_node = await SpotifyAlbum(
                        spotify_id=album_data['id'],
                        name=album_data['name'],
                        album_type=album_data['album_type'],
                        release_date=album_data['release_date'],
                        total_tracks=album_data['total_tracks'],
                        uri=album_data['uri'],
                        spotify_url=album_data['external_urls']['spotify'],
                        images= [image['url'] for image in album_data['images']],
                        image_heights =[image['height'] for image in album_data['images']],
                        image_widthes = [image['width'] for image in album_data['images']]
                    ).save()
                await node.album.connect(album_node)
                logger.debug('Track connected to Album: %s -> %s', track_data['name'], album_data['name'])

                # Link track to artists
                for artist_data in track_data['artists']:
                    artist_node = await SpotifyArtist.nodes.get_or_none(spotify_id=artist_data['id'])
                    if not artist_node:
                        logger.debug('Creating new Artist node for track: %s', artist_data['name'])
                        artist_node = await SpotifyArtist(
                            spotify_id=artist_data['id'],
                            name=artist_data['name'],
                            uri=artist_data['uri'],
                            spotify_url=artist_data['external_urls']['spotify'],
                            href= artist_data['href'],
                            type = artist_data['type']
                        ).save()
                    await node.artists.connect(artist_node)
                    logger.debug('Track connected to Artist: %s -> %s', track_data['name'], artist_data['name'])

            elif label == 'Genre':
                genre_data = item[0]
                logger.debug('Processing Genre: %s', genre_data)
                node = await SpotifyGenre.nodes.get_or_none(name=genre_data)
                if not node:
                    logger.debug('Creating new Genre node: %s', genre_data)
                    node = await SpotifyGenre(name=genre_data).save()
                logger.debug('connecting top Genre node: %s', user.likes_genres)
                if relation_type == "top":
                    await user.likes_genres.connect(node)
                elif relation_type == "followed":
                    await user.likes_genres.connect(node)
                logger.debug('Genre processed: %s', genre_data)

            elif label == 'Album':
                album_data = item
                logger.debug('Processing Album: %s', album_data['name'])
                node = await SpotifyAlbum.nodes.get_or_none(spotify_id=album_data['id'])
                if not node:
                    logger.debug('Creating new Album node: %s', album_data['name'])
                    node = await SpotifyAlbum(
                        spotify_id=album_data['id'],
                        name=album_data['name'],
                        album_type=album_data['album_type'],
                        release_date=album_data['release_date'],
                        total_tracks=album_data['total_tracks'],
                        uri=album_data['uri'],
                        spotify_url=album_data['external_urls']['spotify'],
                        images= [image['url'] for image in album_data['images']],
                        image_heights =[image['height'] for image in album_data['images']],
                        image_widthes = [image['width'] for image in album_data['images']]
                    ).save()
                if relation_type == "saved":
                    await user.likes_albums.connect(node)
                logger.debug('Album processed: %s', album_data['name'])

        logger.info('Items mapped to Neo4j successfully for user=%s, label=%s, relation_type=%s', user, label, relation_type)

    async def clear_user_likes(self, user):
        logger.debug('Clearing user likes for user=%s', user)
        
        # Clear relationships for top artists, tracks, genres, followed artists, saved tracks, albums, and played tracks
        await asyncio.gather(
            user.top_artists.disconnect_all(),
            user.likes_artists.disconnect_all(),
            user.likes_tracks.disconnect_all(),
            user.likes_genres.disconnect_all(),
            user.likes_albums.disconnect_all(),
            user.played_tracks.disconnect_all()
        )
        logger.info('User likes cleared successfully for user=%s', user)

    async def save_user_likes(self, user):
        logger.debug('Saving user likes for user=%s', user)

        # Clear existing likes
        await self.clear_user_likes(user)
        
        user_top_artists = await self.fetch_with_retries(self.fetch_top_artists(user))
        user_top_tracks = await self.fetch_with_retries(self.fetch_top_tracks(user))
        user_top_genres = await self.fetch_with_retries(self.fetch_top_genres(user))
        user_followed_artists = await self.fetch_with_retries(self.fetch_followed_artists(user))
        user_followed_genres = await self.fetch_with_retries(self.fetch_followed_genres(user))  
        user_saved_tracks = await self.fetch_with_retries(self.fetch_saved_tracks(user))
        user_saved_albums = await self.fetch_with_retries(self.fetch_saved_albums(user))
        user_played_tracks = await self.fetch_with_retries(self.fetch_recently_played(user))  
        
        # Map data to Neo4j
        await asyncio.gather(
            self.map_to_neo4j(user, 'Artist', user_top_artists, "top"),
            self.map_to_neo4j(user, 'Track', user_top_tracks, "top"),
            self.map_to_neo4j(user, 'Genre', user_top_genres, "top"),
            self.map_to_neo4j(user, 'Artist', user_followed_artists, "followed"),
            self.map_to_neo4j(user, 'Genre', user_followed_genres, "followed"),
            self.map_to_neo4j(user, 'Track', user_saved_tracks, "saved"),
            self.map_to_neo4j(user, 'Album', user_saved_albums, "saved"),
            self.map_to_neo4j(user, 'Track', user_played_tracks, "played")
        )
        logger.info('User likes saved successfully for user=%s', user)

    async def refresh_token(self, user):
        logger.debug('Refreshing token for user=%s', user)
        tokens = await self.refresh_access_token(user.refresh_token)
        logger.info('Token refreshed successfully for user=%s', user)
        return tokens
