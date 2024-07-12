
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
    @abstractmethod
    def map_to_neo4j(self, user, label, items, source):
        raise NotImplementedError
