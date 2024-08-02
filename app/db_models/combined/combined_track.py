from ..spotify.spotify_track import SpotifyTrack
from ..ytmusic.ytmusic_track import YtmusicTrack
from ..lastfm.lastfm_track import LastfmTrack

class CombinedTrack(SpotifyTrack, YtmusicTrack, LastfmTrack):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }