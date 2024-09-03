from neomodel import StringProperty,IntegerProperty,ArrayProperty, AsyncStructuredNode, AsyncRelationshipTo

from ..artist import Artist
import logging
logger = logging.getLogger('app')


class SpotifyArtist(Artist):
    spotify_id = StringProperty(unique_index=True)
    href = StringProperty( unique_index=True, max_length=255,default="")
    popularity = IntegerProperty( min_value=1, max_value=255,default=0)
    type = StringProperty( max_length=255,default="")
    uri = StringProperty( max_length=255,default="")
    spotify_url = StringProperty()
    followers = IntegerProperty()
    images = ArrayProperty()
    genres = ArrayProperty()
    image_heights = ArrayProperty()
    image_widthes = ArrayProperty()
    images = AsyncRelationshipTo('.spotify_image.SpotifyImage', 'HAS_IMAGE')


    async def serialize(self):
        base_data = await super().serialize()
        spotify_data = {
            'spotify_id': self.spotify_id,
            'spotify_url': self.spotify_url,
            'href': self.href,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri,
            'followers': self.followers,
            'images': self.images,
            'image_heights' : self.image_heights,
            'image_widthes' : self.image_widthes,
            'genres': self.genres
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
