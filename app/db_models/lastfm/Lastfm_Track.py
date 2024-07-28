from neomodel import ( StringProperty)
from ..Track import Track


class LastfmTrack(Track):
    lastfm_id = StringProperty(unique_index=True)
    name = StringProperty()
    
    async def serialize(self):
        return {
            'uid': self.uid,
            'lastfm_id': self.lastfm_id,
            'name': self.name,
            }