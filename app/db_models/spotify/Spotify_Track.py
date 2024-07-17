from neomodel import ( StringProperty,IntegerProperty,BooleanProperty,ArrayProperty)
from ..Track import Track



class SpotifyTrack(Track):
    spotify_id = StringProperty()
    href = StringProperty( min_length=1, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( min_length=1, max_length=255)
    uri = StringProperty( min_length=1, max_length=255)
    duration_ms = IntegerProperty()
    disc_number = IntegerProperty()
    explicit = BooleanProperty()
    isrc = StringProperty()
    upc=StringProperty()
    preview_url = StringProperty()
    track_number = IntegerProperty()
    spotify_url = StringProperty()
    
    
    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'spotify_id':self.spotify_id,
            'href':self.href,
            'popularity':self.popularity,
            'type':self.type,
            'uri':self.uri,
            'duration_ms':self.duration_ms,
            'disc_number':self.disc_number,
            'explicit':self.explicit,
            'preview_url':self.preview_url,
            'track_number':self.track_number,
            'spotify_url':self.spotify_url,
           
            

        }

    