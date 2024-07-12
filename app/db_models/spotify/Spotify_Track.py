from neomodel import ( StringProperty,IntegerProperty,BooleanProperty)
from ..Track import Track



class SpotifyTrack(Track):
    spotify_id = StringProperty()
    href = StringProperty( min_length=1, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( min_length=1, max_length=255)
    uri = StringProperty( min_length=1, max_length=255)
    duration_ms = IntegerProperty()
    disc_number = IntegerProperty()
    explicit = BooleanProperty()
    isrc = StringProperty()
    preview_url = StringProperty()
    track_number = IntegerProperty()
    spotify_url = StringProperty()
    
    