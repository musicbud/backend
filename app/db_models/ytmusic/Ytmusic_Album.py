from neomodel import StringProperty,ArrayProperty

from ..Album import Album


class YtmusicAlbum(Album):
    ytmusic_id =StringProperty() 
    browseId = StringProperty(unique_index=True)
    thumbnails = ArrayProperty()

    
    
