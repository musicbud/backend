from neomodel import StringProperty,ArrayProperty

from ..Track import Track


class YtmusicTrack(Track):
    videoId = StringProperty(unique_index=True)
    thumbnails = ArrayProperty()
    thumbnails = ArrayProperty()
    thumbnail_heights = ArrayProperty()
    thumbnail_widthes = ArrayProperty()


    async def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'videoId':self.videoId,
            'thumbnails':self.thumbnails,
            'thumbnail_heights':self.thumbnail_heights,
            'thumbnail_widthes':self.thumbnail_widthes
            

        }


    
    
