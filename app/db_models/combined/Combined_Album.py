from ..spotify.Spotify_Album import SpotifyAlbum
from ..ytmusic.Ytmusic_Album import YtmusicAlbum
from ..lastfm.Lastfm_Album import LastfmAlbum

class CombinedAlbum(SpotifyAlbum, YtmusicAlbum, LastfmAlbum):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }