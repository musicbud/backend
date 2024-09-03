import logging
from neomodel import db, StructuredNode
from django.conf import settings

logger = logging.getLogger(__name__)

def resolve_node_class(labels):
    label_set = frozenset(labels)
    if {'LastfmTrack', 'LikedItem', 'SpotifyTrack', 'Track', 'YtmusicTrack', 'CombinedTrack'}.issubset(label_set):
        from app.db_models.combined.combined_track import CombinedTrack
        return CombinedTrack
    if {'SpotifyTrack', 'Track'}.issubset(label_set):
        from app.db_models.spotify.spotify_track import SpotifyTrack
        return SpotifyTrack
    if {'LastfmTrack', 'Track'}.issubset(label_set):
        from app.db_models.lastfm.lastfm_track import LastfmTrack
        return LastfmTrack
    if {'YtmusicTrack', 'Track'}.issubset(label_set):
        from app.db_models.ytmusic.ytmusic_track import YtmusicTrack
        return YtmusicTrack
    # Add more custom resolutions here if needed
    return None

def custom_install_labels():
    from neomodel import db, RelationshipTo, RelationshipFrom
    from app.db_models.spotify.spotify_user import SpotifyUser
    from app.db_models.spotify.spotify_artist import SpotifyArtist
    from app.db_models.spotify.spotify_track import SpotifyTrack
    from app.db_models.spotify.spotify_album import SpotifyAlbum
    from app.db_models.spotify.spotify_genre import SpotifyGenre
    from app.db_models.spotify.spotify_image import SpotifyImage
    from app.db_models.liked_item import LikedItem
    from app.db_models.artist import Artist
    from app.db_models.track import Track
    from app.db_models.album import Album

    def install_labels(cls, quiet=False, stdout=None):
        if not hasattr(cls, '__label__'):
            return

        label = cls.__label__
        properties = cls.defined_properties(aliases=False, properties=False)
        for name, property in properties.items():
            if not isinstance(property, (RelationshipTo, RelationshipFrom)):
                if hasattr(property, 'unique_index') and property.unique_index:
                    query = f"CREATE CONSTRAINT ON (n:{label}) ASSERT n.{name} IS UNIQUE"
                    try:
                        db.cypher_query(query)
                        if not quiet:
                            print(f" + Creating node unique constraint for {name} on label {label} for class {cls.__module__}.{cls.__name__}", file=stdout)
                    except Exception as e:
                        print(f" ! Error creating constraint for {name} on label {label}: {str(e)}", file=stdout)

    for cls in [SpotifyUser, SpotifyArtist, SpotifyTrack, SpotifyAlbum, SpotifyGenre, SpotifyImage, LikedItem, Artist, Track, Album]:
        install_labels(cls)

    logger.info("All labels installed successfully.")

# Set the Neo4j connection
db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)

# Set the node class resolver
db.node_class_registry = resolve_node_class