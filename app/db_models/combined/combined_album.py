from ..spotify.spotify_album import SpotifyAlbum
from ..ytmusic.ytmusic_album import YtmusicAlbum
from ..lastfm.lastfm_album import LastfmAlbum

class CombinedAlbum(SpotifyAlbum, YtmusicAlbum, LastfmAlbum):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }