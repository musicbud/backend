from neomodel import StringProperty,ArrayProperty

from ..Artist import Artist


class YtmusicArtist(Artist):
    ytmusic_id =StringProperty() 
    browse_id = StringProperty(unique_index=True)
    thumbnails = ArrayProperty()
