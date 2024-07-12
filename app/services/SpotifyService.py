from .ServiceStrategy import ServiceStrategy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Tuple

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

    def fetch_top_artists(self, user,limit=10,time_range='long_term'):
        sp = spotipy.Spotify(auth=user.access_token)
        top_artists = sp.current_user_top_artists(limit=limit,time_range=time_range)['items']
        artist_names = [artist['name'] for artist in top_artists]
        return artist_names

    def fetch_top_tracks(self, user,limit=10,time_range='long_term'):
        sp = spotipy.Spotify(auth=user.access_token)
        top_tracks = sp.current_user_top_tracks(limit=limit,time_range=time_range)['items']
        track_names = [track['name'] for track in top_tracks]
        return track_names

    def fetch_top_genres(self, user,limit=10):
        top_artists = self.fetch_top_artists( user,limit)
        genre_count = {}
        for artist in top_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        genre_names = [genre[0] for genre in top_genres]
        return genre_names

    # def get_user_top_artists_and_tracks(self, access_token, time_range='long_term', limit=50):
    #     sp = spotipy.Spotify(auth=access_token)
    #     user_top_artists = sp.current_user_top_artists(time_range=time_range, limit=limit)['items']
    #     user_top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)['items']
    #     return user_top_artists, user_top_tracks

    # def fetch_common_artists_tracks_and_genres(self, access_token, artist_ids, track_ids,genre_ids):
    #     sp = spotipy.Spotify(auth=access_token)
    #     common_artists_data = self._fetch_artists(sp, artist_ids)
    #     common_tracks_data = self._fetch_tracks(sp, track_ids)
    #     common_genres_data = self._fetch_genres(sp, genre_ids)
    #     return common_artists_data, common_tracks_data,common_genres_data

    def save_user_likes(self, user):
        user_top_artists = self.fetch_top_artists(user)
        user_top_tracks = self.fetch_top_tracks(user)
        user_top_genres = self.fetch_top_genres(user)

        print(user_top_artists)
        print(user_top_tracks)
        print(user_top_genres)

        
        # Extract artist, track, and genre names
        artist_names = [artist['name'] for artist in user_top_artists]
        track_names = [track['name'] for track in user_top_tracks]
        genre_names = [genre[0] for genre in user_top_genres]
        
        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', artist_names, 'Spotify')
        self.map_to_neo4j(user, 'Track', track_names, 'Spotify')
        self.map_to_neo4j(user, 'Genre', genre_names, 'Spotify')

    def refresh_token(self,user):
        return self.auth_manager.refresh_access_token(user.refresh_token)
        