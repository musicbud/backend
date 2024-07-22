from django.http import JsonResponse
from app.db_models.combined.CombinedArtist import CombinedArtist
from app.db_models.combined.CombinedTrack import CombinedTrack
from app.db_models.combined.CombinedGenre import CombinedGenre
from app.db_models.combined.CombinedAlbum import CombinedAlbum
from app.db_models.spotify.Spotify_Artist import SpotifyArtist
from app.db_models.lastfm.Lastfm_Artist import LastfmArtist
from app.db_models.ytmusic.Ytmusic_Artist import YtmusicArtist
from app.db_models.spotify.Spotify_Track import SpotifyTrack
from app.db_models.lastfm.Lastfm_Track import LastfmTrack
from app.db_models.ytmusic.Ytmusic_Track import YtmusicTrack
from app.db_models.spotify.Spotify_Genre import SpotifyGenre
from app.db_models.lastfm.Lastfm_Genre import LastfmGenre
from app.db_models.spotify.Spotify_Album import SpotifyAlbum
from app.db_models.lastfm.Lastfm_Album import LastfmAlbum
from app.db_models.ytmusic.Ytmusic_Album import YtmusicAlbum
from app.db_models.User import User
from django.db import transaction


import logging
logger = logging.getLogger(__name__)

from neomodel import StructuredNode, RelationshipFrom, RelationshipTo
from collections import defaultdict
from neomodel import db

def merge_similars(request):
    labels = {
        'Artist': ['SpotifyArtist', 'YtmusicArtist', 'LastfmArtist'],
        'Track': ['SpotifyTrack', 'LastfmTrack', 'YtmusicTrack'],
        'Genre': ['SpotifyGenre', 'LastfmGenre'],
        'Album': ['SpotifyAlbum', 'LastfmAlbum', 'YtmusicAlbum']
    }
    
    all_nodes = defaultdict(list)
    
    for model_type, model_labels in labels.items():
        for label in model_labels:
            cypher_query = f"MATCH (n:{label}) RETURN n"
            result, _ = db.cypher_query(cypher_query)
            for record in result:
                node = inflate_node(record[0], model_type)
                if node:
                    all_nodes[model_type].append(node)

    for model_type, nodes in all_nodes.items():
        nodes_by_name = defaultdict(list)
        for item in nodes:
            nodes_by_name[item.name].append(item)

        duplicate_nodes = {name: nodes for name, nodes in nodes_by_name.items() if len(nodes) > 1}

        for name, nodes in duplicate_nodes.items():
            merge_nodes(model_type, nodes)

    return JsonResponse({
        'message': 'Merged similars successfully.',
        'code': 200,
        'status': 'HTTP OK',
    })


def merge_nodes(model_type, nodes):
    if len(nodes) <= 1:
        return

    combined_node = create_combined_node(model_type, nodes)

    for node in nodes:
        if node != combined_node:
            node.delete()


def inflate_node(record, model_type):
    if model_type == 'Artist':
        if 'SpotifyArtist' in record.labels:
            return SpotifyArtist.inflate(record)
        elif 'YtmusicArtist' in record.labels:
            return YtmusicArtist.inflate(record)
        elif 'LastfmArtist' in record.labels:
            return LastfmArtist.inflate(record)
    elif model_type == 'Track':
        if 'SpotifyTrack' in record.labels:
            return SpotifyTrack.inflate(record)
        elif 'LastfmTrack' in record.labels:
            return LastfmTrack.inflate(record)
        elif 'YtmusicTrack' in record.labels:
            return YtmusicTrack.inflate(record)
    elif model_type == 'Genre':
        if 'SpotifyGenre' in record.labels:
            return SpotifyGenre.inflate(record)
        elif 'LastfmGenre' in record.labels:
            return LastfmGenre.inflate(record)
    elif model_type == 'Album':
        if 'SpotifyAlbum' in record.labels:
            return SpotifyAlbum.inflate(record)
        elif 'LastfmAlbum' in record.labels:
            return LastfmAlbum.inflate(record)
        elif 'YtmusicAlbum' in record.labels:
            return YtmusicAlbum.inflate(record)
    return None
def create_combined_node(model_type, nodes):
    combined_node_data = {
        'uid': nodes[0].uid,
        'name': nodes[0].name
    }

    combined_node_cls = {
        'Artist': CombinedArtist,
        'Track': CombinedTrack,
        'Genre': CombinedGenre,
        'Album': CombinedAlbum
    }[model_type]

    combined_node = combined_node_cls(**combined_node_data).save()

    properties_to_add = defaultdict(set)
    list_properties_to_add = defaultdict(list)
    relationships_to_merge = defaultdict(lambda: defaultdict(set))

    for node in nodes:
        if not isinstance(node, StructuredNode):
            continue

        for prop_name, _ in node.__all_properties__:
            value = getattr(node, prop_name, None)
            if value is not None:
                if isinstance(value, list):
                    list_properties_to_add[prop_name].extend(value)
                else:
                    properties_to_add[prop_name].add(value)

        for rel_name, rel_obj in node.__all_relationships__:
            try:
                related_nodes = getattr(node, rel_name).all() if hasattr(node, rel_name) else None
                if related_nodes:
                    related_node_class = type(related_nodes[0]).__name__
                    relationships_to_merge[rel_name][related_node_class].update(related_node.uid for related_node in related_nodes)
            except AttributeError as e:
                logger.error(f"Error accessing relationship {rel_name} on {node}: {str(e)}")
                continue

    for prop_name, values in properties_to_add.items():
        if values:
            setattr(combined_node, prop_name, next(iter(values)))

    for prop_name, values in list_properties_to_add.items():
        if values:
            merged_value = list(set(values))
            setattr(combined_node, prop_name, merged_value)

    combined_node.save()

    OUTGOING = 1
    INCOMING = -1

    with transaction.atomic():
        for rel_name, related_node_classes in relationships_to_merge.items():
            rel_obj = getattr(combined_node, rel_name, None)
            if rel_obj is None:
                logger.error(f"Relationship {rel_name} not found on {combined_node_cls}.")
                continue

            rel_def = getattr(combined_node_cls, rel_name, None)
            if rel_def is None:
                logger.error(f"Relationship definition for {rel_name} not found in {combined_node_cls}.")
                continue

            rel_direction = rel_def.definition.get('direction', None)

            if rel_direction is None:
                logger.error(f"Direction for relationship {rel_name} not found in definition.")
                continue

            for related_node_class, related_node_ids in related_node_classes.items():
                related_node_cls = {
                    'SpotifyArtist': SpotifyArtist,
                    'YtmusicArtist': YtmusicArtist,
                    'LastfmArtist': LastfmArtist,
                    'SpotifyTrack': SpotifyTrack,
                    'LastfmTrack': LastfmTrack,
                    'YtmusicTrack': YtmusicTrack,
                    'SpotifyGenre': SpotifyGenre,
                    'LastfmGenre': LastfmGenre,
                    'SpotifyAlbum': SpotifyAlbum,
                    'LastfmAlbum': LastfmAlbum,
                    'YtmusicAlbum': YtmusicAlbum
                }.get(related_node_class)

                if related_node_cls:
                    for related_node_id in related_node_ids:
                        try:
                            related_node = related_node_cls.nodes.get(uid=related_node_id)

                            if rel_direction == OUTGOING:  # OUTGOING
                                if not rel_obj.is_connected(related_node):
                                    logger.debug(f"Connecting {combined_node} to {related_node}")
                                    rel_obj.__getattribute__(rel_name).connect(related_node)
                            elif rel_direction == INCOMING:  # INCOMING
                                if not related_node.__getattribute__(rel_name).is_connected(combined_node):
                                    logger.debug(f"Connecting {related_node} to {combined_node}")
                                    related_node.__getattribute__(rel_name).connect(combined_node)
                        except related_node_cls.DoesNotExist:
                            logger.error(f"Node with ID {related_node_id} does not exist in class {related_node_class}.")
                        except AttributeError as e:
                            logger.error(f"Error accessing relationship {rel_name} on related node: {str(e)}")

    combined_node.save()
    return combined_node
