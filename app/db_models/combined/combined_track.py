from neomodel import RelationshipTo, StringProperty
from app.db_models.track import Track
from app.db_models.ytmusic.ytmusic_track import YtmusicTrack
from app.db_models.lastfm.lastfm_track import LastfmTrack
from app.db_models.spotify.spotify_track import SpotifyTrack

class CombinedTrack(Track):
    combined_id = StringProperty(unique_index=True)
    ytmusic_track = RelationshipTo(YtmusicTrack, 'YTMUSIC_TRACK', cardinality=1)
    lastfm_track = RelationshipTo(LastfmTrack, 'LASTFM_TRACK', cardinality=1)
    spotify_track = RelationshipTo(SpotifyTrack, 'SPOTIFY_TRACK', cardinality=1)

    @property
    def ytmusic_track_data(self):
        return self.ytmusic_track.single()

    @property
    def lastfm_track_data(self):
        return self.lastfm_track.single()

    @property
    def spotify_track_data(self):
        return self.spotify_track.single()