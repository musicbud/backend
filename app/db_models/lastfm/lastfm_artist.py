from neomodel import StringProperty

from ..artist import Artist

class LastfmArtist(Artist):
    lastfm_id = StringProperty(unique_index=True)
    name = StringProperty()

    
    async def serialize(self):
        return {
            'uid': self.uid,
            'lastfm_id': self.lastfm_id,
            'name': self.name,
            }