from .ServiceStrategy import ServiceStrategy
import pylast
from typing import List, Tuple
import os 
# Strategy for Last.fm

class LastFmService(ServiceStrategy):
    """
    An implementation of the AuthStrategy abstract base class for Last.fm API authentication and data retrieval.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the LastFmAuthService with the provided API key and secret.
        Sets up the network and session key.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_key_file = os.path.join(os.path.expanduser("~"), ".lastfm_session_key")
        self.network = pylast.LastFMNetwork(api_key=self.api_key, api_secret=self.api_secret)
    
    def get_user_profile(self,token) -> dict:
        network = pylast.LastFMNetwork(api_key=self.api_key, api_secret=self.api_secret,token=token)
        username =  network.get_authenticated_user().get_name()
        return {
        'username': username,
        }
    def create_authorize_url(self) -> str:
        """
        Generates a URL for user authorization.
        """
        skg = pylast.SessionKeyGenerator(self.network)
        return skg.get_web_auth_url()

    def fetch_top_artists(self, username: str, limit: int = 10) -> List[pylast.TopItem]:
        """
        Fetches the top artists for a given user.
        """
        return self.network.get_user(username).get_top_artists(limit=limit)

    def fetch_top_tracks(self, username: str, limit: int = 10) -> List[pylast.TopItem]:
        """
        Fetches the top tracks for a given user.
        """
        # Ensure limit is an integer
        limit = int(limit)  # Convert limit to integer if it's passed as a string or other type
        
        return self.network.get_user(username).get_top_tracks(limit=limit)

    def fetch_top_genres(self, username: str, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Fetches the top genres for a given user based on their top artists' tags.
        """
        top_artists = self.fetch_top_artists(username, limit)
        genre_count = {}
        
        for artist in top_artists:
            tags = artist.item.get_top_tags(limit=5)
            for tag in tags:
                
                genre = tag.item.get_name()
                if genre in genre_count:
                    genre_count[genre] += tag.weight
                else:
                    genre_count[genre] = tag.weight
        
        # Convert dictionary to list of tuples for sorting
        sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:limit]        
        return sorted_genres
    def fetch_library(self, username: str):
        user = self.network.get_user(username)
        library = user.get_library()
        return library

    def fetch_top_charts(self, limit: int = 10):
        top_tracks = self.network.get_top_tracks(limit=limit)
        top_artists = self.network.get_top_artists(limit=limit)
        return top_tracks, top_artists

    def save_user_likes(self, user):
        user_top_artists =  self.fetch_top_artists(user.username)
        user_top_tracks =  self.fetch_top_tracks(user.username)
        user_top_genres =  self.fetch_top_genres(user.username)
        
        # Extract artist, track, genre, album, and band names
        artist_names = [artist.item.get_name() for artist in user_top_artists]
        track_names = [track.item.get_name() for track in user_top_tracks]
        genre_names = [genre[0] for genre in user_top_genres]
        
        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', artist_names, 'LastFM')
        self.map_to_neo4j(user, 'Track', track_names, 'LastFM')
        self.map_to_neo4j(user, 'Genre', genre_names, 'LastFM')
