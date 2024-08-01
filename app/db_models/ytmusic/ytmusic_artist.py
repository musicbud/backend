from neomodel import StringProperty,ArrayProperty,IntegerProperty

from ..artist import Artist


class YtmusicArtist(Artist):
    ytmusic_id =StringProperty() 
    browseId = StringProperty(unique_index=True)
    subscribers = StringProperty() 
    thumbnails = ArrayProperty()
    thumbnail_heights = ArrayProperty()
    thumbnail_widthes = ArrayProperty()

    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'ytmusic_id':self.ytmusic_id,
            'browseId':self.browseId,
            'subscribers':self.subscribers,
            'thumbnails':self.thumbnails,
            'thumbnail_heights':self.thumbnail_heights,
            'thumbnail_widthes':self.thumbnail_widthes
            

        }

