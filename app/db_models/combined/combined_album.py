from app.db_models.spotify.spotify_album import SpotifyAlbum
from app.db_models.ytmusic.ytmusic_album import YtmusicAlbum
from app.db_models.lastfm.lastfm_album import LastfmAlbum
from neomodel import StructuredNode, RelationshipTo

class CombinedAlbum(StructuredNode):
    spotify_album = RelationshipTo('app.db_models.spotify.SpotifyAlbum', 'HAS_SPOTIFY_ALBUM')
    ytmusic_album = YtmusicAlbum()
    lastfm_album = LastfmAlbum()

    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'spotify': self.spotify_album.serialize(),
            'ytmusic': self.ytmusic_album.serialize(),
            'lastfm': self.lastfm_album.serialize(),
        }