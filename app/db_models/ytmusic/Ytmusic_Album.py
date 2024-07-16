from neomodel import StringProperty,ArrayProperty

from ..Album import Album


class YtmusicAlbum(Album):
    ytmusic_id =StringProperty() 
    browseId = StringProperty(unique_index=True)
    thumbnails = ArrayProperty()
    thumbnail_heights = ArrayProperty()
    thumbnail_widthes = ArrayProperty()


    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'ytmusic_id':self.ytmusic_id,
            'browseId':self.browseId,
            'thumbnails':self.thumbnails,
            'thumbnail_heights':self.thumbnail_heights,
            'thumbnail_widthes':self.thumbnail_widthes
            

        }

    

    
    
