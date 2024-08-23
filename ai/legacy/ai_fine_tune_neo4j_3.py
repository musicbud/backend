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
    
    item_dict_artist, item_dict_artist_reversed = await regenerate_dictionary('item_dict_artist.pkl', 'item_dict_artist_reversed.pkl', 'artist')
    item_dict_track, item_dict_track_reversed = await regenerate_dictionary('item_dict_track.pkl', 'item_dict_track_reversed.pkl', 'track')
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

    # Create item features as tuples (item_id, features)
    num_features = 10
    feature_names = [f"feature_{i}" for i in range(num_features)]
    item_features = [(name, {feature_name: np.random.rand() for feature_name in feature_names}) for name in item_names]

    # Create user features as tuples (user_id, features)
    user_features = [(uid, {feature_name: np.random.rand() for feature_name in feature_names}) for uid in user_ids]

    # Create a mapping of item names to indices
    item_name_to_index = {name: index for index, name in enumerate(item_names)}
    logger.debug(f"Item Name to Index Mapping: {item_name_to_index}")

    # Create a list of all item IDs
    all_item_ids = list(item_name_to_index.values())

    # Fit the dataset with users and items
    dataset.fit(users=user_ids, items=all_item_ids)

    # Create item features matrix manually
    item_features_matrix = np.zeros((len(item_names), num_features))
    for i, (name, features) in enumerate(item_features):
        for j, feature_name in enumerate(feature_names):
            item_features_matrix[i, j] = features[feature_name]

    # Create user features matrix manually
    user_features_matrix = np.zeros((len(user_ids), num_features))
    for i, (uid, features) in enumerate(user_features):
        for j, feature_name in enumerate(feature_names):
            user_features_matrix[i, j] = features[feature_name]

    # Convert item features matrix to sparse matrix
    item_features_matrix_sparse = sp.csr_matrix(item_features_matrix)

    # Convert user features matrix to sparse matrix
    user_features_matrix_sparse = sp.csr_matrix(user_features_matrix)
    # Create interactions list
    interactions = []
    for user in users:
        user_tracks = await user.likes_tracks.all()
        user_artists = await user.likes_artists.all()

        for track in user_tracks:
            track_idx = item_name_to_index.get(track.name)
            if track_idx is not None:
                interactions.append((user.uid, track_idx))
            else:
                logger.warning(f"Track '{track.name}' not found in item dictionary.")

        for artist in user_artists:
            artist_idx = item_name_to_index.get(artist.name)
            if artist_idx is not None:
                interactions.append((user.uid, artist_idx))
            else:
                logger.warning(f"Artist '{artist.name}' not found in item dictionary.")

    logger.debug(f"Interactions: {interactions}")

    if not interactions:
        logger.error("No interactions found.")
        return None, None, None, None

    try:
        interactions_matrix, _ = dataset.build_interactions(interactions)
        logger.info("Interactions matrix built successfully.")
        return interactions_matrix, dataset, item_features_matrix_sparse, user_features_matrix_sparse
    except Exception as e:
        logger.error(f"Error building interactions matrix: {e}")
        return None, None, None, None

async def get_custom_user_data(user_id):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        liked_artists = await user.likes_artists.all()
        liked_tracks = await user.likes_tracks.all()

        liked_artist_names = [artist.name.strip() for artist in liked_artists] if liked_artists is not None else []
        liked_track_names = [track.name.strip() for track in liked_tracks] if liked_tracks is not None else []

        if not liked_artist_names:
            logger.error(f"No liked artist names found for user ID {user_id}.")
        if not liked_track_names:
            logger.error(f"No liked track names found for user ID {user_id}.")

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

async def get_recommendations(user_id):
    try:
        liked_artist_names, liked_track_names = await get_custom_user_data(user_id)
        artist_indices, track_indices = map_data_to_indices(liked_artist_names, liked_track_names)

        if not artist_indices and not track_indices:
            logger.warning(f"No valid artist or track indices found for user ID {user_id}.")
            return [], []

        # Generate user features
        num_features = len(item_dict_artist) + len(item_dict_track)
        user_features_matrix = np.zeros((1, num_features))
        user_features_matrix[0, artist_indices + track_indices] = 1

        # Get all item IDs
        all_item_ids = np.array(range(len(item_dict_artist) + len(item_dict_track)))

        # Make predictions on a single user feature and all item IDs
        predictions_artist = model_artist.predict(user_features_matrix[0], all_item_ids)
        predictions_track = model_track.predict(user_features_matrix[0], all_item_ids)
        predictions = predictions_artist + predictions_track

        # Select the top-N items with the highest scores
        top_n = 10
        top_recommendations = np.argsort(-predictions)[:top_n]

        logger.debug(f"Predictions: {predictions}")
        logger.debug(f"Top Recommendations: {top_recommendations}")

        # Get item names for recommendations
        recommended_items = [item_dict_artist_reversed.get(idx) or item_dict_track_reversed.get(idx) for idx in top_recommendations]
        return recommended_items
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []
    
async def fine_tune_model(model, interactions_matrix, dataset, item_features_matrix=None, user_features_matrix=None):
    try:
        model = LightFM(learning_rate=0.05, loss='warp')
        model.fit(interactions_matrix, item_features=item_features_matrix, user_features=user_features_matrix, epochs=10)
        logger.info("Model fine-tuned successfully.")
        return model
    except Exception as e:
        logger.error(f"Error fine-tuning model: {e}")
        return None

async def run():
    await setup_dictionaries()
    interactions_matrix, dataset, item_features, user_features = await build_interaction_matrix()
    if interactions_matrix is not None:
        model = await fine_tune_model(LightFM(), interactions_matrix, dataset, item_features, user_features)
        if model:
            recommendations = await get_recommendations('33a55ade4b204e84a6c4c681bd751479')
            logger.info(f"Recommendations: {recommendations}")

if __name__ == '__main__':
    asyncio.run(run())
