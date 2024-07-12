from neomodel import  StringProperty,IntegerProperty,ArrayProperty
from ..Album import Album

class SpotifyAlbum(Album):
    spotify_id = StringProperty()
    name = StringProperty(required=True)
    href = StringProperty()
    album_type = StringProperty()
    release_date = StringProperty()
    total_tracks = IntegerProperty()
    uri = StringProperty()
    spotify_url = StringProperty()
    images = ArrayProperty()

    