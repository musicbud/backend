from ..spotify.Spotify_Track import SpotifyTrack
from ..ytmusic.Ytmusic_Track import YtmusicTrack
from ..lastfm.Lastfm_Track import LastfmTrack

class CombinedTrack(SpotifyTrack, YtmusicTrack, LastfmTrack):
    

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
        }