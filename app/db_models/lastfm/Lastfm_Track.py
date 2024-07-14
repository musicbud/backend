from neomodel import ( StringProperty)
from ..Track import Track


class LastfmTrack(Track):
    lastfm_id = StringProperty(unique_index=True, required=True)