
from abc import ABC, abstractmethod

class ServiceStrategy(ABC):
    @abstractmethod
    def create_authorize_url(self):
        pass
    @abstractmethod
    def map_to_neo4j(self, user, label, items, source):
        raise NotImplementedError
