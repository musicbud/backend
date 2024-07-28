from ..spotify.Spotify_Artist import SpotifyArtist
from ..ytmusic.Ytmusic_Artist import YtmusicArtist
from ..lastfm.Lastfm_Artist import LastfmArtist

class CombinedArtist(SpotifyArtist, YtmusicArtist, LastfmArtist):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }