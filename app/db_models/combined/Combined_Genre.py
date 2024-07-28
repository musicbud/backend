from ..spotify.Spotify_Genre import SpotifyGenre
from ..lastfm.Lastfm_Genre import LastfmGenre

class CombinedGenre(SpotifyGenre, LastfmGenre):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }