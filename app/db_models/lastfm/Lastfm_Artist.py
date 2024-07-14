from neomodel import StringProperty

from ..Artist import Artist

class LastfmArtist(Artist):
    lastfm_id = StringProperty(unique_index=True, required=True)
    
