from neomodel import AsyncStructuredNode, StringProperty, IntegerProperty, BooleanProperty, AsyncRelationshipTo, AsyncRelationshipFrom
from ..track import Track
import logging
logger = logging.getLogger('app')

class SpotifyTrack(Track):
    spotify_id = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    uri = StringProperty()
    spotify_url = StringProperty()
    href = StringProperty(default="")
    duration_ms = IntegerProperty()
    popularity = IntegerProperty(default=0)
    preview_url = StringProperty(default="")
    track_number = IntegerProperty()
    disc_number = IntegerProperty()
    explicit = BooleanProperty()
    type = StringProperty(default="track")
    is_local = BooleanProperty()
    isrc = StringProperty() 
    element_id_property = StringProperty()

    album = AsyncRelationshipTo('app.db_models.spotify.spotify_album.SpotifyAlbum', 'BELONGS_TO')
    artists = AsyncRelationshipTo('app.db_models.spotify.spotify_artist.SpotifyArtist', 'PERFORMED_BY')
    images = AsyncRelationshipTo('app.db_models.spotify.spotify_image.SpotifyImage', 'HAS_IMAGE')

    async def serialize(self):
        base_data = await super().serialize()
        spotify_data =  {
            'spotify_id': self.spotify_id,
            'name': self.name,
            'uri': self.uri,
            'spotify_url': self.spotify_url,
            'href': self.href,
            'duration_ms': self.duration_ms,
            'popularity': self.popularity,
            'preview_url': self.preview_url,
            'track_number': self.track_number,
            'disc_number': self.disc_number,
            'explicit': self.explicit,
            'type': self.type,
            'is_local': self.is_local,
            'isrc': self.isrc  ,
            'element_id_property': self.element_id_property,
        }
        images = await self.images.all()
        serialized_images = []
        for image in images:
            try:    
                serialized_image = await image.serialize()
                serialized_images.append(serialized_image)
            except Exception as e:
                logger.error(f"Error serializing image: {str(e)}")

        spotify_data['images'] = serialized_images

        return {**base_data, **spotify_data}



