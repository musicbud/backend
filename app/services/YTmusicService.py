from .ServiceStrategy import ServiceStrategy
from google_auth_oauthlib.flow import InstalledAppFlow
import ytmusicapi 
from typing import List, Tuple

from app.db_models.ytmusic.Ytmusic_Artist import YtmusicArtist
from app.db_models.ytmusic.Ytmusic_Track import YtmusicTrack
from app.db_models.ytmusic.Ytmusic_Album import YtmusicAlbum

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
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES,redirect_uri=self.redirect_uri)
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
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES,redirect_uri=self.redirect_uri)
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
    
    def fetch_library_artists(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the library artists for a user.
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
            
           

    def fetch_library_tracks(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the library tracks for a user.
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

    def fetch_library_albums(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the library albums for a user.
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
    
    def fetch_liked_tracks(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the liked songs for a user.
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
        return ytmusic.get_liked_songs(limit=limit)['tracks']
    
    def fetch_library_subscriptions(self, user: str, limit: int = 10) -> List[str]:
        """
        Fetches and maps the liked songs for a user.
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
        return ytmusic.get_library_subscriptions(limit=limit)
    
    def fetch_history(self, user):
        """
        Fetches and maps the liked songs for a user.
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
        return ytmusic.get_history()


    def map_to_neo4j(self, user, label, items, relation_type):
        
        for item in items:
            node = None
            if label == 'Artist':
                # Check if the artist already exists
                node = YtmusicArtist.nodes.get_or_none(name=item['artist'])
                if not node:
                    node = YtmusicArtist(name=item['artist'],browse_id =item['browseId'] ,thumbnails=[image['url'] for image in item['thumbnails']]).save()
                

                if relation_type == "library":
                    relationship = user.library_artists.relationship(node)
                    if relationship is None:
                        relationship = user.library_artists.connect(node)
                elif relation_type == "subscribed":
                    relationship = user.subscriptions.relationship(node)
                    if relationship is None:
                        relationship = user.subscriptions.connect(node)
                
            elif label == 'Track':
                # Check if the track already exists
                node = YtmusicTrack.nodes.get_or_none(name=item['title'])
                if not node:
                    node = YtmusicTrack(name=item['title'],video_id =item['videoId'] ,thumbnails=[image['url'] for image in item['thumbnails']]).save()
                
                # Link track to artists
                for artist in item['artists']:
                    artist_node = YtmusicArtist.nodes.get_or_none(name=artist['name'],ytmusic_id= artist['id'])
                    if artist_node:
                        node.artists.connect(artist_node)
                # Link track to album
                album = item['album']
                album_node = YtmusicAlbum.nodes.get_or_none(name=album['name'],ytmusic_id= album['id'])
                if album_node:
                    node.album.connect(album_node)                
                if relation_type == "library":
                    relationship = user.library_tracks.relationship(node)
                    if relationship is None:
                        relationship = user.library_tracks.connect(node)
                elif relation_type == "liked":
                    relationship = user.likes_track.relationship(node)
                    if relationship is None:
                        relationship = user.likes_track.connect(node)
                elif relation_type == "played":
                    relationship = user.played_track.relationship(node)
                    if relationship is None:
                        relationship = user.played_track.connect(node)
                
            elif label == 'Album':
                # Check if the album already exists
                node = YtmusicAlbum.nodes.get_or_none(name=item['title'])
                if not node:
                    node = YtmusicAlbum(name=item['title'],browse_id =item['browseId'] ,thumbnails=[image['url'] for image in item['thumbnails']]).save()
                # Link album to artists
                for artist in item['artists']:
                    artist_node = YtmusicArtist.nodes.get_or_none(name=artist['name'],ytmusic_id= artist['id'])
                    if artist_node:
                        node.artists.connect(artist_node)
                
                relationship = user.library_albums.relationship(node)
                if relationship is None:
                    relationship = user.library_albums.connect(node)

    def save_user_likes(self, user):
        user_library_artists = self.fetch_library_artists(user)
        user_library_tracks = self.fetch_library_tracks(user)
        user_library_albums = self.fetch_library_albums(user)
        user_liked_tracks = self.fetch_liked_tracks(user)
        user_library_subscriptions = self.fetch_library_subscriptions(user)
        user_history = self.fetch_history(user)
    

        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', user_library_artists,'library')
        self.map_to_neo4j(user, 'Track', user_library_tracks,'library') 
        self.map_to_neo4j(user, 'Album', user_library_albums,'library')
        self.map_to_neo4j(user, 'Track', user_liked_tracks,'liked') 
        self.map_to_neo4j(user, 'Artist', user_library_subscriptions,'subscribed')
        self.map_to_neo4j(user, 'Track', user_history,'played')



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