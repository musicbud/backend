from ..spotify.spotify_genre import SpotifyGenre
from ..lastfm.lastfm_genre import LastfmGenre

class CombinedGenre(SpotifyGenre, LastfmGenre):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }