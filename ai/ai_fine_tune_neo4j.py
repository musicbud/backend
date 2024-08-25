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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables and set up database connection
load_dotenv()
config.DATABASE_URL = os.getenv('NEOMODEL_NEO4J_BOLT_URL')
db.set_connection(config.DATABASE_URL)

# Add the project directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models
from app.db_models.spotify.spotify_user import SpotifyUser
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack

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

async def get_liked_items(user_id, item_type):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        if item_type == 'artists':
            liked_items = await user.likes_artists.all()
        elif item_type == 'tracks':
            liked_items = await user.likes_tracks.all()
        else:
            raise ValueError("Invalid item type")
        logger.debug(f"Liked {item_type.capitalize()}: {liked_items}")
        return liked_items
    except Exception as e:
        logger.error(f"Error retrieving liked {item_type} for user ID {user_id}: {e}")
        return []

def map_items_to_indices(items, item_dict):
    """Map a list of item objects to their corresponding indices."""
    item_indices = []
    for item in items:
        index = item_dict.get(item.name)
        if index is not None:
            item_indices.append(index)
        else:
            logger.warning(f"Item name '{item.name}' not found in index mapping.")
    return item_indices

async def build_interaction_matrix():
    """
    Builds a custom interaction matrix from Neo4j data.
    """
    users = await SpotifyUser.nodes.all()
    tracks = await SpotifyTrack.nodes.all()
    artists = await SpotifyArtist.nodes.all()

    dataset = Dataset()

    user_ids = [user.uid for user in users]
    item_names = [track.name for track in tracks] + [artist.name for artist in artists]

    dataset.fit(users=user_ids, items=item_names)

    interactions = []
    for user in users:
        user_tracks = await user.likes_tracks.all()
        user_artists = await user.likes_artists.all()

        interactions.extend((user.uid, track.name) for track in user_tracks)
        interactions.extend((user.uid, artist.name) for artist in user_artists)

    logger.debug(f"Interactions: {interactions}")

    if not interactions:
        logger.error("No interactions found.")
        return None, None, None, None

    try:
        interactions_matrix, _ = dataset.build_interactions(interactions)
        logger.info("Interactions matrix built successfully.")

        item_features_matrix = sp.identity(len(item_names), format='csr')
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

        user_item_indices = artist_indices + [idx + len(item_dict_artist) for idx in track_indices]

        num_features = item_features_matrix_sparse.shape[0]

        user_feature_vector = np.zeros(num_features)
        user_feature_vector[user_item_indices] = 1

        logger.debug(f"User Feature Vector Shape: {user_feature_vector.shape}")
        logger.debug(f"User Feature Vector: {user_feature_vector}")

        user_index = user_dict[user_id]
        item_ids = np.arange(num_features)

        item_scores = model_artist.predict(user_index, item_ids)

        top_items = np.argsort(item_scores)[::-1]
        logger.debug(f"Top Items: {top_items}")

        recommended_artists = [item_dict_artist_reversed.get(idx) for idx in top_items[:10] if idx in item_dict_artist_reversed]
        recommended_tracks = [item_dict_track_reversed.get(idx - len(item_dict_artist)) for idx in top_items[:10] if (idx - len(item_dict_artist)) in item_dict_track_reversed]

        logger.debug(f"Recommended Artists: {recommended_artists}")
        logger.debug(f"Recommended Tracks: {recommended_tracks}")

        recommended_users = []
        for other_user_id, other_user_index in user_dict.items():
            if other_user_id == user_id:
                continue

            other_user_feature_vector = np.zeros(num_features)
            nonzero_indices = user_features_matrix_sparse[other_user_index].nonzero()[1]
            if nonzero_indices.size == 0:
                logger.warning(f"User {other_user_id} has no non-zero features.")
                continue
            other_user_feature_vector[nonzero_indices] = 1

            logger.debug(f"Other User Feature Vector for {other_user_id}: {other_user_feature_vector}")

            if user_feature_vector.shape != other_user_feature_vector.shape:
                logger.error(f"Shape mismatch: user_feature_vector.shape {user_feature_vector.shape} != other_user_feature_vector.shape {other_user_feature_vector.shape}")
                continue

            match_score = np.dot(user_feature_vector, other_user_feature_vector)
            user_feature_vector_sum = np.sum(user_feature_vector)

            if user_feature_vector_sum == 0:
                logger.error(f"User feature vector sum is zero for user ID {user_id}.")
                continue

            match_percentage = match_score / user_feature_vector_sum * 100

            logger.debug(f"Match Percentage for {other_user_id}: {match_percentage}")

            if match_percentage > 0:
                recommended_users.append((other_user_id, match_percentage))

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

    recommended_artists, recommended_tracks, recommended_users = loop.run_until_complete(get_recommendations(
        user_id, item_features_matrix_sparse, user_features_matrix_sparse
    ))

    logger.info(f"Recommended Artists: {recommended_artists}")
    logger.info(f"Recommended Tracks: {recommended_tracks}")
    logger.info(f"Recommended Users: {recommended_users}")