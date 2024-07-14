from neomodel import  StringProperty
from ..Album import Album

class LastfmAlbum(Album):
    lastfm_id = StringProperty(unique_index=True, required=True)   