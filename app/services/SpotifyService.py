from .ServiceStrategy import ServiceStrategy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Tuple

from app.db_models.spotify.Spotify_Artist import SpotifyArtist
from app.db_models.spotify.Spotify_Track import SpotifyTrack
from app.db_models.spotify.Spotify_Genre import SpotifyGenre
from app.db_models.spotify.Spotify_Album import SpotifyAlbum

from django.http import JsonResponse

class SpotifyService(ServiceStrategy):
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.auth_manager = SpotifyOAuth(client_id=self.client_id,
                                         client_secret=self.client_secret,
                                         redirect_uri=self.redirect_uri,
                                         scope=self.scope)
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
    
    def create_authorize_url(self):
        return self.auth_manager.get_authorize_url()
    
    def get_tokens(self, code):
        return self.auth_manager.get_access_token(code=code, check_cache=False)
    def refresh_access_token(self, refresh_token):
        token_info = self.auth_manager.refresh_access_token(refresh_token)
        return token_info

    def get_user_profile(self, tokens):
        sp = spotipy.Spotify(auth=tokens['access_token'])
        return sp.current_user()

    def fetch_top_artists(self, user,limit=50,time_range='long_term'):
        sp = spotipy.Spotify(auth=user.access_token)
        return  sp.current_user_top_artists(limit=limit,time_range=time_range)['items']

    def fetch_top_tracks(self, user,limit=50,time_range='long_term'):
        sp = spotipy.Spotify(auth=user.access_token)
        return sp.current_user_top_tracks(limit=limit,time_range=time_range)['items']

    def fetch_top_genres(self, user,limit=50):
        top_artists = self.fetch_top_artists( user,limit)
        genre_count = {}
        for artist in top_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def fetch_followed_artists(self, user, limit=50):
        sp = spotipy.Spotify(auth=user.access_token)
        return sp.current_user_followed_artists(limit=limit)['artists']['items']

    def fetch_saved_tracks(self, user, limit=50):
        sp = spotipy.Spotify(auth=user.access_token)
        return [item['track'] for item in sp.current_user_saved_tracks(limit=limit)['items']]

    def fetch_saved_albums(self, user, limit=50):
        sp = spotipy.Spotify(auth=user.access_token)
        return [item['album'] for item in sp.current_user_saved_albums(limit=limit)['items']]
    
    def fetch_followed_genres(self, user,limit=50):
        followed_artists = self.fetch_followed_artists( user,limit)
        genre_count = {}
        for artist in followed_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    def map_to_neo4j(self, user, label, items, relation_type="top"):

        for item in items:
            node = None

            if label == 'Artist':
                artist_data = item
                node = SpotifyArtist.nodes.get_or_none(spotify_id=artist_data['id'])
                if not node:
                    node = SpotifyArtist(
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
                    user.top_artists.connect(node)
                elif relation_type == "followed":
                    user.likes_artists.connect(node)

            elif label == 'Track':
                track_data = item
                node = SpotifyTrack.nodes.get_or_none(spotify_id=track_data['id'])
                if not node:
                    node = SpotifyTrack(
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
                    user.top_tracks.connect(node)
                elif relation_type == "saved":
                    user.likes_tracks.connect(node)

                # Link track to album
                album_data = track_data['album']
                album_node = SpotifyAlbum.nodes.get_or_none(spotify_id=album_data['id'])
                if not album_node:
                    album_node = SpotifyAlbum(
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
                node.album.connect(album_node)

                # Link track to artists
                for artist_data in track_data['artists']:
                    artist_node = SpotifyArtist.nodes.get_or_none(spotify_id=artist_data['id'])
                    if not artist_node:
                        artist_node = SpotifyArtist(
                        spotify_id=artist_data['id'],
                        name=artist_data['name'],
                        uri=artist_data['uri'],
                        spotify_url=artist_data['external_urls']['spotify'],
                        href= artist_data['href'],
                        type = artist_data['type']
                        ).save()
                    node.artists.connect(artist_node)

            elif label == 'Genre':
                genre_data = item[0]
                node = SpotifyGenre.nodes.get_or_none(name=genre_data)
                if not node:
                    node = SpotifyGenre(name=genre_data).save()
                if relation_type == "top":
                    user.top_genres.connect(node)
                elif relation_type == "followed":
                    user.likes_genres.connect(node)

            elif label == 'Album':
                album_data = item
                node = SpotifyAlbum.nodes.get_or_none(spotify_id=album_data['id'])
                if not node:
                    node = SpotifyAlbum(
                        spotify_id=album_data['id'],
                        name=album_data['name'],
                        album_type=album_data['album_type'],
                        release_date=album_data['release_date'],
                        total_tracks=album_data['total_tracks'],
                        uri=album_data['uri'],
                        spotify_url=album_data['external_urls']['spotify'],
                        genres= [genre[0] for genre in album_data['genres']],
                        images= [image['url'] for image in album_data['images']],
                        image_heights =[image['height'] for image in album_data['images']],
                        image_widthes = [image['width'] for image in album_data['images']]

                    ).save()
                if relation_type == "top":
                    user.top_albums.connect(node)
                elif relation_type == "saved":
                    user.likes_albums.connect(node)

    def save_user_likes(self, user):
        user_top_artists = self.fetch_top_artists(user)
        user_top_tracks = self.fetch_top_tracks(user)
        user_top_genres = self.fetch_top_genres(user)
        user_followed_artists = self.fetch_followed_artists(user)  
        user_followed_genres = self.fetch_followed_genres(user)  
        user_saved_tracks = self.fetch_saved_tracks(user)
        user_saved_albums = self.fetch_saved_albums(user)  

        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', user_top_artists, "top")
        self.map_to_neo4j(user, 'Track', user_top_tracks, "top")
        self.map_to_neo4j(user, 'Genre', user_top_genres, "top")
        self.map_to_neo4j(user, 'Artist', user_followed_artists, "followed")
        self.map_to_neo4j(user, 'Genre', user_followed_genres, "followed")
        self.map_to_neo4j(user, 'Track', user_saved_tracks, "saved")
        self.map_to_neo4j(user, 'Album', user_saved_albums, "saved")


    def refresh_token(self,user):
        return self.auth_manager.refresh_access_token(user.refresh_token)
            