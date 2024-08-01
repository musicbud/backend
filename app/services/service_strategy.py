
from abc import ABC, abstractmethod

class ServiceStrategy(ABC):
    @abstractmethod
    def create_authorize_url(self):
        pass
    