from neomodel import StringProperty

from ..Artist import Artist

class LastfmArtist(Artist):
    lastfm_id = StringProperty(unique_index=True, required=True)
    
    def serialize(self):
        return {
            'uid': self.uid,
            'lastfm_id': self.lastfm_id,
            'name': self.name,
            }