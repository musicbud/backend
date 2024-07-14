from neomodel import StringProperty,ArrayProperty

from ..Track import Track


class YtmusicTrack(Track):
    videoId = StringProperty(unique_index=True)
    thumbnails = ArrayProperty()

    
    
