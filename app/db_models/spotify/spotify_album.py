from neomodel import StructuredNode, StringProperty, IntegerProperty, AsyncRelationshipTo, ArrayProperty, AsyncRelationshipFrom
from ..album import Album

class SpotifyAlbum(Album):
    spotify_id = StringProperty(unique_index=True)
    name = StringProperty(required=True)
    href = StringProperty()
    label = StringProperty()
    album_type = StringProperty()
    release_date = StringProperty()
    release_date_precision = StringProperty()
    total_tracks = IntegerProperty()
    uri = StringProperty()
    spotify_url = StringProperty()
    upc= StringProperty()
    total_tracks=IntegerProperty()

    artists = AsyncRelationshipTo('app.db_models.spotify.spotify_artist.SpotifyArtist', 'CREATED_BY')
    tracks = AsyncRelationshipFrom('app.db_models.spotify.spotify_track.SpotifyTrack', 'BELONGS_TO')
    images = AsyncRelationshipTo('app.db_models.spotify.spotify_image.SpotifyImage', 'HAS_IMAGE')

    
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
            'images': [await image.serialize() for image in await self.images.all()],
        }