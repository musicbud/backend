from neomodel import StringProperty,IntegerProperty

from ..Artist import Artist


class SpotifyArtist(Artist):
    spotify_id = StringProperty()
    browse_id = StringProperty(unique_index=True)
    href = StringProperty( unique_index=True, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( max_length=255)
    uri = StringProperty( max_length=255)
    spotify_url = StringProperty()
