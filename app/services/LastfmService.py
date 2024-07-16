from .ServiceStrategy import ServiceStrategy
import pylast
from typing import List, Tuple
import os 

from app.db_models.lastfm.Lastfm_Artist import LastfmArtist
from app.db_models.lastfm.Lastfm_Track import LastfmTrack
from app.db_models.lastfm.Lastfm_Genre import LastfmGenre
from app.db_models.lastfm.Lastfm_Album import LastfmAlbum

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
    
    def fetch_liked_tracks(self, username: str):
        user = self.network.get_user(username)
        loved_tracks = user.get_loved_tracks()
        return loved_tracks
    

    def map_to_neo4j(self, user, label, items,relation_type):
        for item in items:
            node = None
            if label == 'Artist':
                item_name = item.item.get_name()
                item_id = item.item.get_mbid()  if item.item.get_mbid() is not None else item_name
                item_weight = int(item.weight) if item.weight is not None else 0

                node = LastfmArtist.nodes.get_or_none(lastfm_id=item_id)
                if not node:
                    node = LastfmArtist(lastfm_id=item_id, name=item_name).save()

                if relation_type == "top":
                    relationship = user.top_artists.relationship(node)
                    if relationship is None:
                        relationship = user.top_artists.connect(node)
                elif relation_type == "loved":
                    relationship = user.likes_artist.relationship(node)
                    if relationship is None:
                        relationship = user.likes_artist.connect(node)
                relationship.weight = item_weight
                relationship.save()

            elif label == 'Track':
                item_name = item.item.get_name()
                item_id = item.item.get_mbid()  if item.item.get_mbid() is not None else item_name
                item_weight = int(item.weight) if item.weight is not None else 0
                
                node = LastfmTrack.nodes.get_or_none(lastfm_id=item_id)
                if not node:
                    node = LastfmTrack(lastfm_id=item_id, name=item_name).save()
                if relation_type == "top":
                    relationship = user.top_tracks.relationship(node)
                    if relationship is None:
                        relationship = user.top_tracks.connect(node)
                elif relation_type == "loved":
                    relationship = user.likes_track.relationship(node)
                    if relationship is None:
                        relationship = user.likes_track.connect(node)
                relationship.weight = item_weight
                relationship.save()
            
            elif label == 'Album':
                item_name = item.item.get_name()
                item_id = item.item.get_mbid()  if item.item.get_mbid() is not None else item_name
                item_weight = int(item.weight) if item.weight is not None else 0
                
                node = LastfmAlbum.nodes.get_or_none(lastfm_id=item_id)
                if not node:
                    node = LastfmAlbum(lastfm_id=item_id, name=item_name).save()
                if relation_type == "top":
                    relationship = user.top_albums.relationship(node)
                    if relationship is None:
                        relationship = user.top_albums.connect(node)
                elif relation_type == "loved":
                    relationship = user.likes_album.relationship(node)
                    if relationship is None:
                        relationship = user.likes_album.connect(node)
                relationship.weight = item_weight
                relationship.save()
                
            elif label == 'Genre':
                item_name = item[0]
                item_weight = item[1]

                
                node = LastfmGenre.nodes.get_or_none(name=item_name)
                if not node:
                    node = LastfmGenre(name=item_name).save()
                if relation_type == "top":
                    relationship = user.top_genres.relationship(node)
                    if relationship is None:
                        relationship = user.top_genres.connect(node)
                elif relation_type == "loved":
                    relationship = user.likes_genre.relationship(node)
                    if relationship is None:
                        relationship = user.likes_genre.connect(node)
                relationship.weight = item_weight
                relationship.save()
            
    def save_user_likes(self, user):
        
        user_top_artists =  self.fetch_top_artists(user.username)
        user_top_tracks =  self.fetch_top_tracks(user.username)
        user_top_genres =  self.fetch_top_genres(user.username)
        user_liked_tracks =  self.fetch_liked_tracks(user.username)
        
        # Map data to Neo4j
        self.map_to_neo4j(user, 'Artist', user_top_artists,"top")
        self.map_to_neo4j(user, 'Track', user_top_tracks,"top")
        self.map_to_neo4j(user, 'Genre', user_top_genres,"top")
        self.map_to_neo4j(user, 'Track', user_liked_tracks, "loved")
