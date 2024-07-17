from neomodel import StringProperty,IntegerProperty,ArrayProperty

from ..Artist import Artist


class SpotifyArtist(Artist):
    spotify_id = StringProperty()
    href = StringProperty( unique_index=True, max_length=255)
    popularity = IntegerProperty( min_value=1, max_value=255)
    type = StringProperty( max_length=255)
    uri = StringProperty( max_length=255)
    spotify_url = StringProperty()
    followers = IntegerProperty()
    images = ArrayProperty()
    genres = ArrayProperty()
    image_heights = ArrayProperty()
    image_widthes = ArrayProperty()


    def serialize(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'spotify_id':self.spotify_id,
            'href':self.href,
            'popularity':self.popularity,
            'type':self.type,
            'uri':self.uri,
            'spotify_url':self.spotify_url,
            'followers':self.followers,
            'images':self.images,
            'image_heights' : self.image_heights,
            'image_widthes' : self.image_widthes,
            'genres':self.genres
        }
