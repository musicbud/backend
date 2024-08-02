from ..spotify.spotify_artist import SpotifyArtist
from ..ytmusic.ytmusic_artist import YtmusicArtist
from ..lastfm.lastfm_artist import LastfmArtist

class CombinedArtist(SpotifyArtist, YtmusicArtist, LastfmArtist):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }