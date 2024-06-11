from spotipy.oauth2 import SpotifyOAuth
import spotipy
import json
from datetime import datetime
class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri,scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope= scope

        self.auth_manager = SpotifyOAuth(client_id=self.client_id,
                                    client_secret=self.client_secret,
                                    redirect_uri=self.redirect_uri,
                                    scope=self.scope)


    def create_authorize_url(self):
        """
        Create the URL that users will visit to authorize the application.
        :param scope: The requested scopes (permissions) for the application.
                      Defaults to None.
        :return: The authorization URL.
        """

        authorize_url = self.auth_manager.get_authorize_url()
        return authorize_url

    def get_spotify_tokens(self, code):
        """
        Get the Spotify access and refresh tokens using the authorization code.
        :param code: The authorization code obtained from the authorization callback.
        :return: A dictionary containing the access and refresh tokens.
        """

        tokens = self.auth_manager.get_access_token(code = code,check_cache=False)
        return tokens
    
    def get_current_user_profile(self, access_token):
        # Initialize spotipy client with the access token
        sp = spotipy.Spotify(auth=access_token)
        # Fetch the current user's profile
        return sp.current_user()
    
    def refresh_access_token(self, refresh_token):
        sp = spotipy.Spotify(auth_manager=self.auth_manager)
        # get token information
        token_info = sp.auth_manager.get_cached_token()
        refresh_token = token_info['refresh_token']

        sp.auth_manager.refresh_access_token(refresh_token)
        token_info = sp.auth_manager.get_cached_token()
        return token_info
    def get_user_top_artists_and_tracks(self, access_token, time_range='long_term', limit=20):
        sp = spotipy.Spotify(auth=access_token)    
        user_top_artists = sp.current_user_top_artists(time_range=time_range, limit=limit)['items']
        user_top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)['items']
        return user_top_artists, user_top_tracks
    def fetch_common_artists_and_tracks(self, access_token, artist_ids, track_ids):
        self.sp = spotipy.Spotify(auth=access_token)    
        common_artists_data = self.fetch_artists(artist_ids)
        common_tracks_data = self.fetch_tracks(track_ids)
        return common_artists_data, common_tracks_data

    def fetch_artists(self, artist_ids):
        artists_data = []
        if artist_ids:
            artists_data = self.sp.artists(artist_ids)['artists']
        return artists_data

    def fetch_tracks(self, track_ids):
        tracks_data = []
        if track_ids:
            tracks_data = self.sp.tracks(track_ids)['tracks']
        return tracks_data