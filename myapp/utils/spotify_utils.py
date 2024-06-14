import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from datetime import datetime

class SpotifyClient:
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

    def get_spotify_tokens(self, code):
        return self.auth_manager.get_access_token(code=code, check_cache=False)

    def get_current_user_profile(self, access_token):
        sp = spotipy.Spotify(auth=access_token)
        return sp.current_user()

    def refresh_access_token(self, refresh_token):
        token_info = self.auth_manager.refresh_access_token(refresh_token)
        return token_info

    def get_user_top_artists_and_tracks(self, access_token, time_range='long_term', limit=50):
        sp = spotipy.Spotify(auth=access_token)
        user_top_artists = sp.current_user_top_artists(time_range=time_range, limit=limit)['items']
        user_top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)['items']
        return user_top_artists, user_top_tracks

    def fetch_common_artists_tracks_and_genres(self, access_token, artist_ids, track_ids,genre_ids):
        sp = spotipy.Spotify(auth=access_token)
        common_artists_data = self._fetch_artists(sp, artist_ids)
        common_tracks_data = self._fetch_tracks(sp, track_ids)
        common_genres_data = self._fetch_genres(sp, genre_ids)
        return common_artists_data, common_tracks_data,common_genres_data

    def _fetch_artists(self, sp, artist_ids):
        if not artist_ids:
            return []
        artists_info = sp.artists(artist_ids)['artists']
        return [{'id': track['id'],'href': artist['external_urls']['spotify'], 'name': artist['name']} for artist in artists_info]

    def _fetch_tracks(self, sp, track_ids):
        if not track_ids:
            return []
        tracks_info = sp.tracks(track_ids)['tracks']
        return [{ 'id': track['id'],'href': track['external_urls']['spotify'], 'name': track['name']} for track in tracks_info]
    def _fetch_genres(self, sp, genre_ids):
        if not genre_ids:
            return []
        genres_info = sp.genres(genre_ids)['genres']
        return [{ 'id': genre['id'],'href': genre['external_urls']['spotify'], 'name': genre['name']} for genre in genres_info]
