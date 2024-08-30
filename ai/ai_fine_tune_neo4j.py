import numpy as np
import joblib
import sys
import os
from dotenv import load_dotenv
from neomodel import config, db
from lightfm import LightFM
from lightfm.data import Dataset
import asyncio
import logging
import scipy.sparse as sp

# Set up logging
neo4j_logger = logging.getLogger('neo4j')
neo4j_logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up the database connection
config.DATABASE_URL = os.getenv('NEOMODEL_NEO4J_BOLT_URL')
db.set_connection(config.DATABASE_URL)

# Add the project directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models
from app.db_models.spotify.spotify_user import SpotifyUser
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack
from app.db_models.user import User
from app.db_models.liked_item import LikedItem
from app.db_models.artist import Artist
from app.db_models.album import Album
from app.db_models.track import Track
from app.db_models.genre import Genre
from app.db_models.lastfm.lastfm_artist import LastfmArtist
from app.db_models.lastfm.lastfm_track import LastfmTrack
from app.db_models.ytmusic.ytmusic_artist import YtmusicArtist
from app.db_models.ytmusic.ytmusic_track import YtmusicTrack
from app.db_models.combined.combined_artist import CombinedArtist
from app.db_models.combined.combined_track import CombinedTrack
from app.db_models.parent_user import ParentUser

# Load the trained models
try:
    model_artist = joblib.load('model_artist.pkl')
    model_track = joblib.load('model_track.pkl')
except Exception as e:
    logger.error(f"Error loading models: {e}")
    sys.exit(1)

# Initialize global dictionaries
item_dict_artist = joblib.load('item_dict_artist.pkl')
item_dict_artist_reversed = joblib.load('item_dict_artist_reversed.pkl')
item_dict_track = joblib.load('item_dict_track.pkl')
item_dict_track_reversed = joblib.load('item_dict_track_reversed.pkl')
user_dict = joblib.load('user_dict.pkl')
user_dict_reversed = joblib.load('user_dict_reversed.pkl')

async def regenerate_dictionary(item_dict_path, item_dict_reversed_path, item_type):
    async def fetch_items():
        if item_type == 'artist':
            return [artist.name for artist in await SpotifyArtist.nodes.all()]
        elif item_type == 'track':
            return [track.name for track in await SpotifyTrack.nodes.all()]
        else:
            raise ValueError("Invalid item type")

    try:
        items = await fetch_items()
        item_dict = {name: idx for idx, name in enumerate(set(items))}
        item_dict_reversed = {idx: name for name, idx in item_dict.items()}

        joblib.dump(item_dict, item_dict_path)
        joblib.dump(item_dict_reversed, item_dict_reversed_path)

        logger.info(f"{item_type.capitalize()} dictionaries regenerated and saved.")
        return item_dict, item_dict_reversed

    except Exception as e:
        logger.error(f"Error regenerating dictionary for {item_type}: {e}")
        return {}, {}

async def setup_dictionaries():
    global item_dict_artist, item_dict_artist_reversed
    global item_dict_track, item_dict_track_reversed
    global user_dict, user_dict_reversed
    
    item_dict_artist, item_dict_artist_reversed = await regenerate_dictionary('item_dict_artist.pkl', 'item_dict_artist_reversed.pkl', 'artist')
    item_dict_track, item_dict_track_reversed = await regenerate_dictionary('item_dict_track.pkl', 'item_dict_track_reversed.pkl', 'track')
    
    users = await SpotifyUser.nodes.all()
    user_ids = [user.uid for user in users]
    user_dict = {uid: idx for idx, uid in enumerate(user_ids)}
    user_dict_reversed = {idx: uid for uid, idx in user_dict.items()}
    
    joblib.dump(user_dict, 'user_dict.pkl')
    joblib.dump(user_dict_reversed, 'user_dict_reversed.pkl')

async def get_liked_artists(user_id):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        liked_artists = await user.likes_artists.all()
        logger.debug(f"Liked Artists: {liked_artists}")
        return liked_artists
    except Exception as e:
        logger.error(f"Error retrieving liked artists for user ID {user_id}: {e}")
        return []

async def get_liked_tracks(user_id):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        liked_tracks = await user.likes_tracks.all()
        logger.debug(f"Liked Tracks: {liked_tracks}")
        return liked_tracks
    except Exception as e:
        logger.error(f"Error retrieving liked tracks for user ID {user_id}: {e}")
        return []

def map_artist_names_to_indices(artists):
    """Map a list of artist objects to their corresponding indices."""
    artist_indices = []
    for artist in artists:
        index = item_dict_artist.get(artist.name)
        if index is not None:
            artist_indices.append(index)
        else:
            logger.warning(f"Artist name '{artist.name}' not found in index mapping.")
    return artist_indices

def map_track_names_to_indices(tracks):
    """Map a list of track objects to their corresponding indices."""
    track_indices = []
    for track in tracks:
        index = item_dict_track.get(track.name)
        if index is not None:
            track_indices.append(index)
        else:
            logger.warning(f"Track name '{track.name}' not found in index mapping.")
    return track_indices

async def build_interaction_matrix():
    """
    Builds a custom interaction matrix from Neo4j data.
    """
    users = await SpotifyUser.nodes.all()
    tracks = await SpotifyTrack.nodes.all()
    artists = await SpotifyArtist.nodes.all()

    # Create dataset
    dataset = Dataset()

    # Extract user IDs and item names
    user_ids = [user.uid for user in users]
    track_names = [track.name for track in tracks]
    artist_names = [artist.name for artist in artists]
    item_names = track_names + artist_names

    # Fit the dataset with users and items
    dataset.fit(users=user_ids, items=item_names)

    # Create interactions list
    interactions = []
    for user in users:
        user_tracks = await user.likes_tracks.all()
        user_artists = await user.likes_artists.all()

        for track in user_tracks:
            interactions.append((user.uid, track.name))

        for artist in user_artists:
            interactions.append((user.uid, artist.name))

    logger.debug(f"Interactions: {interactions}")

    if not interactions:
        logger.error("No interactions found.")
        return None, None, None, None

    try:
        interactions_matrix, _ = dataset.build_interactions(interactions)
        logger.info("Interactions matrix built successfully.")

        # Prepare item features matrix
        item_features_matrix = sp.identity(len(item_names), format='csr')
        # Prepare user features matrix
        user_features_matrix = sp.identity(len(user_ids), format='csr')

        return interactions_matrix, dataset, item_features_matrix, user_features_matrix
    except Exception as e:
        logger.error(f"Error building interactions matrix: {e}")
        return None, None, None, None

async def get_custom_user_data(user_id):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        liked_artists = await user.likes_artists.all()
        liked_tracks = await user.likes_tracks.all()

        liked_artist_names = [artist.name.strip() for artist in liked_artists] if liked_artists else []
        liked_track_names = [track.name.strip() for track in liked_tracks] if liked_tracks else []

        return liked_artist_names, liked_track_names
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        return [], []

def map_data_to_indices(liked_artist_names, liked_track_names):
    artist_indices = [item_dict_artist.get(name) for name in liked_artist_names if item_dict_artist.get(name) is not None]
    track_indices = [item_dict_track.get(name) for name in liked_track_names if item_dict_track.get(name) is not None]

    logger.debug(f"Mapped Artist Indices: {artist_indices}")
    logger.debug(f"Mapped Track Indices: {track_indices}")

    return artist_indices, track_indices

async def get_recommendations(user_id, item_features_matrix_sparse, user_features_matrix_sparse):
    try:
        liked_artist_names, liked_track_names = await get_custom_user_data(user_id)
        artist_indices, track_indices = map_data_to_indices(liked_artist_names, liked_track_names)

        if not artist_indices and not track_indices:
            logger.warning(f"No valid artist or track indices found for user ID {user_id}.")
            return [], [], []

        # Combine artist and track indices for user features
        user_item_indices = artist_indices + [idx + len(item_dict_artist) for idx in track_indices]

        # Get the number of features (items)
        num_features = item_features_matrix_sparse.shape[0]  # Number of items in the matrix

        # Generate a single user feature vector with the correct size
        user_feature_vector = np.zeros(num_features)
        user_feature_vector[user_item_indices] = 1

        logger.debug(f"User Feature Vector Shape: {user_feature_vector.shape}")

        # Predict scores for all items for the given user
        user_index = user_dict[user_id]  # Map the user_id to the user index in the LightFM model
        item_ids = np.arange(num_features)  # Generate an array of item IDs (indices)

        # Use LightFM model to predict scores for all items
        item_scores = model_artist.predict(user_index, item_ids)

        top_items = np.argsort(item_scores)[::-1]

        logger.debug(f"Top Items: {top_items}")

        recommended_artists = [item_dict_artist_reversed[idx] for idx in top_items[:10] if idx in item_dict_artist_reversed]
        recommended_tracks = [item_dict_track_reversed[idx - len(item_dict_artist)] for idx in top_items[:10] if (idx - len(item_dict_artist)) in item_dict_track_reversed]

        # Recommend users based on percent match
        recommended_users = []
        for other_user_id, other_user_index in user_dict.items():
            if other_user_id == user_id:
                continue

            # Ensure the other user's feature vector is constructed with the same number of features
            other_user_feature_vector = np.zeros(num_features)
            other_user_feature_vector[user_features_matrix_sparse[other_user_index].nonzero()[1]] = 1

            logger.debug(f"Other User Feature Vector Shape: {other_user_feature_vector.shape}")

            # Ensure both vectors have the same shape
            if user_feature_vector.shape != other_user_feature_vector.shape:
                logger.error(f"Shape mismatch: user_feature_vector.shape {user_feature_vector.shape} != other_user_feature_vector.shape {other_user_feature_vector.shape}")
                continue

            match_score = np.dot(user_feature_vector, other_user_feature_vector)
            match_percentage = match_score / np.sum(user_feature_vector) * 100

            if match_percentage > 0:
                recommended_users.append((other_user_id, match_percentage))

        # Sort users by match percentage in descending order
        recommended_users.sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"Recommended Users: {recommended_users}")

        return recommended_artists, recommended_tracks, recommended_users[:10]
    except Exception as e:
        logger.error(f"Error generating recommendations for user ID {user_id}: {e}")
        return [], [], []


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.run_until_complete(setup_dictionaries())

    interactions_matrix, dataset, item_features_matrix_sparse, user_features_matrix_sparse = loop.run_until_complete(build_interaction_matrix())

    user_id = '71599a394df141c387ec6368ac79c9c3'  # replace with actual user ID

    recommended_users,recommended_artists, recommended_tracks = loop.run_until_complete(get_recommendations(
        user_id, item_features_matrix_sparse, user_features_matrix_sparse
    ))

    logger.info(f"Recommended Artists: {recommended_artists}")
    logger.info(f"Recommended Tracks: {recommended_tracks}")
