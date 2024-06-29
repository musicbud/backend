from .ServiceStrategy import ServiceStrategy
from google_auth_oauthlib.flow import InstalledAppFlow
import ytmusicapi 
from typing import List, Tuple
from myapp.models import User,Artist,Track,Genre,Band,Album
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import time
class YTmusicService(ServiceStrategy):
    """
    A class to interact with YouTube Music's API and integrate data into a Neo4j database.
    """

    def __init__(self,client_id, client_secret,redirect_uri):
        """
        Initializes the YouTube Music API client.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.ytmusic = ytmusicapi.YTMusic()

    def create_authorize_url(self) -> str:
        client_config = {
        "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
        SCOPES = ["openid",'https://www.googleapis.com/auth/userinfo.profile',
                  'https://www.googleapis.com/auth/userinfo.email',
                  'https://www.googleapis.com/auth/youtube.readonly',
                  'https://www.googleapis.com/auth/youtube'
                  ]
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES,redirect_uri='http://127.0.0.1:8000/musicbud/ytmusic/callback')
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
        
    def get_tokens(self, code):
        client_config = {
        "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
        SCOPES = ["openid",'https://www.googleapis.com/auth/userinfo.profile',
                  'https://www.googleapis.com/auth/userinfo.email',
                  'https://www.googleapis.com/auth/youtube.readonly',
                  'https://www.googleapis.com/auth/youtube'
                  ]
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES,redirect_uri='http://127.0.0.1:8000/musicbud/ytmusic/callback')
        return flow.fetch_token(code=code)
    def get_user_profile(self,tokens) -> str:

        token_filtered = {'access_token':tokens['access_token'],
                          'expires_in':tokens['expires_in'],
                          'refresh_token':tokens['refresh_token'],
                          'token_type':tokens['token_type'],
                          'expires_at':tokens['expires_at'],
                          'scope':tokens['scope']
                          }
        return ytmusicapi.YTMusic(auth=token_filtered).get_account_info()  
    
    def fetch_top_artists(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top artists for a user.
        """
        ytmusic = ytmusicapi.YTMusic(
            auth={
                    'access_token':user.access_token,
                    'expires_in':user.expires_in,
                    'refresh_token':user.refresh_token,
                    'token_type': user.token_type,
                    'expires_at':user.expires_at,
                    'scope':user.scope
                })
        return ytmusic.get_library_artists(limit=limit)
            
           

    def fetch_top_tracks(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top tracks for a user.
        """
        ytmusic = ytmusicapi.YTMusic(
            auth={
                    'access_token':user.access_token,
                    'expires_in':user.expires_in,
                    'refresh_token':user.refresh_token,
                    'token_type': user.token_type,
                    'expires_at':user.expires_at,
                    'scope':user.scope
                })
        return ytmusic.get_library_songs(limit=limit)

    def fetch_top_albums(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the top albums for a user.
        """
        ytmusic = ytmusicapi.YTMusic(
            auth={
                    'access_token':user.access_token,
                    'expires_in':user.expires_in,
                    'refresh_token':user.refresh_token,
                    'token_type': user.token_type,
                    'expires_at':user.expires_at,
                    'scope':user.scope
                })
        return ytmusic.get_library_albums(limit=limit)
    
    def save_user_likes(self, user):
        user_top_artists = self.fetch_top_artists(user)
        user_top_tracks = self.fetch_top_tracks(user)
        user_top_albums = self.fetch_top_albums(user)

        # Extract artist, track, genre, album, and band names
        artist_names = [artist for artist in user_top_artists]
        track_names = [track for track in user_top_tracks]
        album_names = [album for album in user_top_albums]

        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', artist_names, 'YTMusic')
        self.map_to_neo4j(user, 'Track', track_names, 'YTMusic') 
        self.map_to_neo4j(user, 'Album', album_names, 'YTMusic')

    def map_to_neo4j(self, user, label, items, source):
        
        for item in items:
            node = None
            if label == 'Artist':
                # Check if the artist already exists
                node = Artist.nodes.get_or_none(name=item['artist'])
                if not node:
                    node = Artist(name=item['artist'],browse_id =item['browseId'] ,source=source).save()
                user.top_artists.connect(node)
                
            elif label == 'Track':
                # Check if the track already exists
                node = Track.nodes.get_or_none(name=item['title'])
                if not node:
                    node = Track(name=item['title'],video_id =item['videoId'] ,source=source).save()
                user.top_tracks.connect(node)
                
            elif label == 'Album':
                # Check if the album already exists
                node = Album.nodes.get_or_none(name=item['title'])
                if not node:
                    node = Album(name=item['title'],browse_id =item['browseId'] ,source=source).save()
                user.top_albums.connect(node)
    def refresh_token(self,user):
            credentials = Credentials(
                token_uri= "https://oauth2.googleapis.com/token",
                client_id= self.client_id,
                client_secret= self.client_secret,
                token = user.access_token,
                refresh_token = user.refresh_token,
                scopes = user.scope,
                expiry= user.expires_at)
            credentials.refresh(Request())
            tokens = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'expires_at':time.mktime(credentials.expiry.timetuple()) if credentials.expiry else None,
                'expires_in':None,
                'token_type':'Bearer',
                'scope': credentials.scopes
            }
            return tokens        