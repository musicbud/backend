from typing import List, Tuple
import os
import time
import pylast
import webbrowser
from myapp.models import User,Artist,Track,Genre,Band,Album
import ytmusicapi 
from abc import ABC, abstractmethod
import subprocess
import re
from musicbud import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi.auth.oauth import OAuthCredentials


class AuthStrategy(ABC):
    @abstractmethod
    def create_authorize_url(self):
        pass
    @abstractmethod
    def fetch_top_artists(self, user, limit=10):
        raise NotImplementedError
    @abstractmethod
    def fetch_top_tracks(self, user, limit=10):
        raise NotImplementedError
    @abstractmethod
    def fetch_top_genres(self, user, limit=10):
        raise NotImplementedError
    @abstractmethod
    def fetch_top_bands(self, user, limit=10):
        raise NotImplementedError
    @abstractmethod
    def fetch_top_albums(self, user, limit=10):
        raise NotImplementedError

    def map_to_neo4j(self, user_name, label, items, source):
        user = User.nodes.get_or_create({'name': user_name})[0]
        for item in items:
            node = None
            if label == 'Artist':
                node = Artist.nodes.get_or_create({'name': item})[0]
                node.add_label(source)
                user.top_artists.connect(node)
            elif label == 'Track':
                node = Track.nodes.get_or_create({'name': item})[0]
                node.add_label(source)
                user.top_tracks.connect(node)
            elif label == 'Genre':
                node = Genre.nodes.get_or_create({'name': item})[0]
                node.add_label(source)
                user.top_genres.connect(node)
            elif label == 'Band':
                node = Band.nodes.get_or_create({'name': item})[0]
                node.add_label(source)
                user.top_bands.connect(node)
            elif label == 'Album':
                node = Album.nodes.get_or_create({'name': item})[0]
                node.add_label(source)
                user.top_albums.connect(node)

# Strategy for Last.fm
class LastFmAuthStrategy(AuthStrategy):
    """
    An implementation of the AuthStrategy abstract base class for Last.fm API authentication and data retrieval.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the LastFmAuthStrategy with the provided API key and secret.
        Sets up the network and session key.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_key_file = os.path.join(os.path.expanduser("~"), ".lastfm_session_key")
        self.network = pylast.LastFMNetwork(api_key=self.api_key, api_secret=self.api_secret)
        self.session_key = self.get_session_key()
        self.network.session_key = self.session_key

    def get_session_key(self) -> str:
        """
        Retrieves or generates a session key for Last.fm API access.
        """
        if not os.path.exists(self.session_key_file):
            skg = pylast.SessionKeyGenerator(self.network)
            url = skg.get_web_auth_url()
            print(f"Please authorize this script to access your account: {url}\n")
            webbrowser.open(url)
            while True:
                print('True')
                try:
                    session_key = skg.get_web_auth_session_key(url)
                    with open(self.session_key_file, "w") as f:
                        f.write(session_key)
                    break
                except pylast.WSError:
                    time.sleep(1)
        else:
            session_key = open(self.session_key_file).read()

        return session_key

    def create_authorize_url(self) -> str:
        """
        Generates a URL for user authorization.
        """
        skg = pylast.SessionKeyGenerator(self.network)
        return skg.get_web_auth_url() + f"&cb={settings.LASTFM_REDIRECT_URI}"

    def fetch_top_artists(self, user: str, limit: int = 10) -> List[pylast.TopItem]:
        """
        Fetches the top artists for a given user.
        """
        return self.network.get_user(user).get_top_artists(limit=limit)

    def fetch_top_tracks(self, user: str, limit: int = 10) -> List[pylast.TopItem]:
        """
        Fetches the top tracks for a given user.
        """
        return self.network.get_user(user).get_top_tracks(limit=limit)

    def fetch_top_genres(self, user: str, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Fetches the top genres for a given user based on their top artists' tags.
        """
        top_artists = self.fetch_top_artists(user, limit)
        genre_count = {}
        for artist in top_artists:
            tags = artist.item.get_top_tags(limit=5)
            for tag in tags:
                genre = tag.item.name
                genre_count[genre] = genre_count.get(genre, 0) + tag.weight
        return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    def fetch_top_albums(self, user, limit=10):
        # Spotify does not have a separate category for bands
        return []
    def fetch_top_bands(self, user, limit=10):
        # Spotify does not have a separate category for bands
        return []

# Strategy for Spotify
class SpotifyAuthStrategy(AuthStrategy):
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

    def get_current_user_profile(self, access_token):
        sp = spotipy.Spotify(auth=access_token)
        return sp.current_user()

    def fetch_top_artists(self, user, limit=10):
        top_artists = self.sp.current_user_top_artists(limit=limit)['items']
        artist_names = [artist['name'] for artist in top_artists]
        self.map_to_neo4j(user, 'Artist', artist_names, 'Spotify')
        return artist_names

    def fetch_top_tracks(self, user, limit=10):
        top_tracks = self.sp.current_user_top_tracks(limit=limit)['items']
        track_names = [track['name'] for track in top_tracks]
        self.map_to_neo4j(user, 'Track', track_names, 'Spotify')
        return track_names

    def fetch_top_genres(self, user, limit=10):
        top_artists = self.fetch_top_artists(user, limit)
        genre_count = {}
        for artist in top_artists:
            for genre in artist['genres']:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        genre_names = [genre[0] for genre in top_genres]
        self.map_to_neo4j(user, 'Genre', genre_names, 'Spotify')
        return genre_names

    def fetch_top_bands(self, user, limit=10):
        # Spotify does not have a separate category for bands
        return []

    def fetch_top_albums(self, user, limit=10):
        top_albums = self.sp.current_user_top_albums(limit=limit)['items']
        album_names = [album['name'] for album in top_albums]
        self.map_to_neo4j(user, 'Album', album_names, 'Spotify')
        return album_names

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

       
class YTmusicAuthStrategy(AuthStrategy):
    """
    A class to interact with YouTube Music's API and integrate data into a Neo4j database.
    """

    def __init__(self,client_id, client_secret):
        """
        Initializes the YouTube Music API client.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.ytmusic = ytmusicapi.YTMusic()

    def create_authorize_url(self) -> str:
        oauth_credentials = OAuthCredentials(self.client_id,self.client_secret)
        code = oauth_credentials.get_code()
        url = f"{code['verification_url']}?user_code={code['user_code']}"

        return url
    def fetch_top_artists(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top artists for a user.
        """
        response = self.ytmusic.get_library_artists(limit=limit)
        top_artists = [artist['name'] for artist in response['results']]
        self.map_to_neo4j(user, 'Artist', top_artists, 'YTMusic')
        return top_artists

    def fetch_top_tracks(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top tracks for a user.
        """
        response = self.ytmusic.get_library_songs(limit=limit)
        top_tracks = [track['title'] for track in response['tracks']]
        self.map_to_neo4j(user, 'Track', top_tracks, 'YTMusic')
        return top_tracks

    def fetch_top_genres(self, user: str, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Fetches and maps the top genres for a user based on the top artists.
        """
        top_artists = self.fetch_top_artists(user, limit)
        genre_count = {}
        for artist in top_artists:
            tags = self.ytmusic.get_artist(artist)['description']
            for tag in tags.split(','):
                genre = tag.strip()
                genre_count[genre] = genre_count.get(genre, 0) + 1
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        self.map_to_neo4j(user, 'Genre', [genre[0] for genre in top_genres], 'YTMusic')
        return top_genres

    def fetch_top_bands(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top bands for a user.
        """
        response = self.ytmusic.get_library_bands(limit=limit)
        top_bands = [band['name'] for band in response['results']]
        self.map_to_neo4j(user, 'Band', top_bands, 'YTMusic')
        return top_bands

    def fetch_top_albums(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top albums for a user.
        """
        response = self.ytmusic.get_library_albums(limit=limit)
        top_albums = [album['title'] for album in response['results']]
        self.map_to_neo4j(user, 'Album', top_albums, 'YTMusic')
        return top_albums

# class AppleMusicAuthStrategy(AuthStrategy):
#     def __init__(self, developer_token, user_token):
#         self.apple_music = AppleMusic(developer_token, user_token)
#     def create_authorize_url(self):
#         # Apple Music uses tokens for authorization
#         return "Apple Music does not require an auth URL"

#     def fetch_top_artists(self, user, limit=10):
#         response = self.apple_music.get_user_top_artists(limit=limit)
#         top_artists = [artist['attributes']['name'] for artist in response['data']]
#         self.map_to_neo4j(user, 'Artist', top_artists, 'AppleMusic')
#         return top_artists

#     def fetch_top_tracks(self, user, limit=10):
#         response = self.apple_music.get_user_top_tracks(limit=limit)
#         top_tracks = [track['attributes']['name'] for track in response['data']]
#         self.map_to_neo4j(user, 'Track', top_tracks, 'AppleMusic')
#         return top_tracks

#     def fetch_top_genres(self, user, limit=10):
#         top_artists = self.fetch_top_artists(user, limit)
#         genre_count = {}
#         for artist in top_artists:
#             tags = artist.get('attributes', {}).get('genreNames', [])
#             for genre in tags:
#                 genre_count[genre] = genre_count.get(genre, 0) + 1
#         top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]
#         genre_names = [genre[0] for genre in top_genres]
#         self.map_to_neo4j(user, 'Genre', genre_names, 'AppleMusic')
#         return genre_names

#     def fetch_top_bands(self, user, limit=10):
#         # Apple Music does not have a separate category for bands
#         return []

#     def fetch_top_albums(self, user, limit=10):
#         response = self.apple_music.get_user_top_albums(limit=limit)
#         top_albums = [album['attributes']['name'] for album in response['data']]
#         self.map_to_neo4j(user, 'Album', top_albums, 'AppleMusic')
#         return top_albums

