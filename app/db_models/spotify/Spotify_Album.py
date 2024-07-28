from neomodel import  StringProperty,IntegerProperty,ArrayProperty
from ..Album import Album

class SpotifyAlbum(Album):
    spotify_id = StringProperty()
    href = StringProperty()
    label = StringProperty()
    album_type = StringProperty()
    release_date = StringProperty()
    total_tracks = IntegerProperty()
    uri = StringProperty()
    spotify_url = StringProperty()
    images = ArrayProperty()
    upc= StringProperty()
    total_tracks=IntegerProperty()
    image_heights = ArrayProperty()
    image_widthes = ArrayProperty()
    
    async def serialize(self):
        return {
            'uid': self.uid,
            'spotify_id': self.spotify_id,
            'name': self.name,
            'href': self.href,
            'label': self.label,
            'album_type' :self.album_type ,
            'release_date' : self.release_date,
            'total_tracks' : self.total_tracks,
            'uri' : self.uri,
            'upc' : self.upc,
            'spotify_url' : self.spotify_url,
            'image_heights' : self.image_heights,
            'image_widthes' : self.image_widthes,
            'artists': [await artist.serialize() for artist in await self.artists.all()],
            'tracks': [await track.serialize() for track in await self.tracks.all()],
        }