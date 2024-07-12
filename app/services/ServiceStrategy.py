from app.db_models.Artist import Artist
from app.db_models.Track import Track
from app.db_models.Genre import Genre
from app.db_models.Band import Band
from app.db_models.Album import Album

from abc import ABC, abstractmethod

class ServiceStrategy(ABC):
    @abstractmethod
    def create_authorize_url(self):
        pass
    @abstractmethod
    def fetch_top_artists(self, user, limit=10):
        raise NotImplementedError
    @abstractmethod
    def fetch_top_tracks(self, user, limit=10):
        raise NotImplementedError

    def map_to_neo4j(self, user, label, items, source):
        
        for item in items:
            node = None
            if label == 'Artist':
                # Check if the artist already exists
                node = Artist.nodes.get_or_none(name=item)
                if not node:
                    node = Artist(name=item, source=source).save()
                user.top_artists.connect(node)
                
            elif label == 'Track':
                # Check if the track already exists
                node = Track.nodes.get_or_none(name=item)
                if not node:
                    node = Track(name=item, source=source).save()
                user.top_tracks.connect(node)
                
            elif label == 'Genre':
                # Check if the genre already exists
                node = Genre.nodes.get_or_none(name=item)
                if not node:
                    node = Genre(name=item, source=source).save()
                user.top_genres.connect(node)
                
            elif label == 'Band':
                # Check if the band already exists
                node = Band.nodes.get_or_none(name=item)
                if not node:
                    node = Band(name=item, source=source).save()
                user.top_bands.connect(node)
                
            elif label == 'Album':
                # Check if the album already exists
                node = Album.nodes.get_or_none(name=item)
                if not node:
                    node = Album(name=item, source=source).save()
                user.top_albums.connect(node)


 
