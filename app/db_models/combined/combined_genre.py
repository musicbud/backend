from neomodel import StructuredNode, StringProperty
from app.db_models.spotify.spotify_genre import SpotifyGenre
from app.db_models.lastfm.lastfm_genre import LastfmGenre

def create_combined_metaclass(*bases):
    metaclasses = set(type(base) for base in bases if isinstance(base, type))
    
    class CombinedMeta(type):
        def __new__(mcls, name, bases, namespace):
            return super().__new__(mcls, name, bases, namespace)

    for metaclass in metaclasses:
        CombinedMeta = type(
            f'Combined{metaclass.__name__}',
            (CombinedMeta, metaclass),
            {}
        )

    return CombinedMeta

CombinedMeta = create_combined_metaclass(SpotifyGenre, LastfmGenre)

class CombinedGenre(SpotifyGenre, LastfmGenre, metaclass=CombinedMeta):
    __label__ = 'CombinedGenre:SpotifyGenre:LastfmGenre'

    name = StringProperty(unique_index=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)