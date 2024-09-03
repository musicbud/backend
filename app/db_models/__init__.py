from .track import Track
from .artist import Artist
from .album import Album
from .genre import Genre
from .spotify.spotify_image import SpotifyImage
from .spotify.spotify_track import SpotifyTrack
from .spotify.spotify_artist import SpotifyArtist
from .spotify.spotify_album import SpotifyAlbum
from .spotify.spotify_genre import SpotifyGenre
from .parent_user import ParentUser
from .ytmusic.ytmusic_track import YtmusicTrack
from .lastfm.lastfm_track import LastfmTrack
from .combined.combined_track import CombinedTrack
from .liked_item import LikedItem
from .spotify.spotify_user import SpotifyUser
# Import other models as needed

default_app_config = 'app.db_models.apps.DbModelsConfig'
