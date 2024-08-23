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
    global user_dict, user_dict_reversed
    
    item_dict_artist, item_dict_artist_reversed = await regenerate_dictionary('item_dict_artist.pkl', 'item_dict_artist_reversed.pkl', 'artist')
    item_dict_track, item_dict_track_reversed = await regenerate_dictionary('item_dict_track.pkl', 'item_dict_track_reversed.pkl', 'track')
    
    users = await SpotifyUser.nodes.all()
    user_ids = [user.uid for user in users]
    user_dict = {uid: idx for idx, uid in enumerate(user_ids)}
    user_dict_reversed = {idx: uid for uid, idx in user_dict.items()}
    
    joblib.dump(user_dict, 'user_dict.pkl')
    joblib.dump(user_dict_reversed, 'user_dict_reversed.pkl')

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
    num_features = len(item_names)
    feature_names = [f"feature_{i}" for i in range(num_features)]
    item_features = [(name, {feature_name: np.random.rand() for feature_name in feature_names}) for name in item_names]

    # Create user features as tuples (user_id, features)
    user_features = [(uid, {feature_name: np.random.rand() for feature_name in feature_names}) for uid in user_ids]

    # Create a mapping of item names to indices
    item_name_to_index = {name: index for index, name in enumerate(item_names)}
    logger.debug(f"Item Name to Index Mapping: {item_name_to_index}")

    # Fit the dataset with users and items
    dataset.fit(users=user_ids, items=item_names)

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
                interactions.append((user.uid, track.name))
            else:
                logger.warning(f"Track '{track.name}' not found in item dictionary.")

        for artist in user_artists:
            artist_idx = item_name_to_index.get(artist.name)
            if artist_idx is not None:
                interactions.append((user.uid, artist.name))
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

        liked_artist_names = [artist.name.strip() for artist in liked_artists] if liked_artists else []
        liked_track_names = [track.name.strip() for track in liked_tracks] if liked_tracks else []

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

async def get_recommendations(user_id, item_features_matrix_sparse, user_features_matrix_sparse):
    try:
        liked_artist_names, liked_track_names = await get_custom_user_data(user_id)
        artist_indices, track_indices = map_data_to_indices(liked_artist_names, liked_track_names)

        if not artist_indices and not track_indices:
            logger.warning(f"No valid artist or track indices found for user ID {user_id}.")
            return [], [], []

        # Concatenate artist and track indices for user features
        user_item_indices = artist_indices + [idx + len(item_dict_artist) for idx in track_indices]

        # Generate a single user feature vector
        user_features_vector = np.zeros((1, item_features_matrix_sparse.shape[1]))
        user_features_vector[0, user_item_indices] = 1

        # Convert the user features vector to sparse format (CSR format)
        user_features_vector_sparse = sp.csr_matrix(user_features_vector)

        # Ensure the number of features in the user and item matrices match
        if user_features_vector_sparse.shape[1] != item_features_matrix_sparse.shape[1]:
            logger.error("User features and item features dimensions do not match.")
            return [], [], []

        # Get all item IDs
        all_artist_ids = np.array(range(len(item_dict_artist)))
        all_track_ids = np.array(range(len(item_dict_track)))
        all_user_ids = np.array(range(len(user_dict)))

        # Make predictions for all items using the sparse matrices
        predictions_artist = model_artist.predict(0, all_artist_ids, item_features=item_features_matrix_sparse, user_features=user_features_vector_sparse)
        predictions_track = model_track.predict(0, all_track_ids, item_features=item_features_matrix_sparse, user_features=user_features_vector_sparse)

        # Select the top-N items with the highest scores
        top_n = 10  # Number of recommendations to return
        top_artists = np.argsort(-predictions_artist)[:top_n]
        top_tracks = np.argsort(-predictions_track)[:top_n]

        # Generate user-user similarity scores
        user_similarities = np.dot(user_features_matrix_sparse, user_features_vector_sparse.T).toarray().flatten()

        # Normalize similarities to percentage
        max_similarity = np.max(user_similarities)
        if max_similarity > 0:
            match_percentages = 100 * user_similarities / max_similarity
        else:
            match_percentages = np.zeros_like(user_similarities)

        # Sort users by similarity
        top_user_indices = np.argsort(-user_similarities)[:top_n]

        # Convert indices back to item names
        top_artist_names = [item_dict_artist_reversed[idx] for idx in top_artists]
        top_track_names = [item_dict_track_reversed[idx] for idx in top_tracks]
        top_user_ids = [user_dict_reversed[idx] for idx in top_user_indices]

        # Return recommendations and similarities
        return top_artist_names, top_track_names, list(zip(top_user_ids, match_percentages[top_user_indices]))

    except Exception as e:
        logger.error(f"Error in getting recommendations: {e}")
        return [], [], []



async def main():
    await setup_dictionaries()
    interactions_matrix, dataset, item_features_matrix_sparse, user_features_matrix_sparse = await build_interaction_matrix()

    if interactions_matrix is None:
        logger.error("Failed to build interaction matrix.")
        return

    user_id = "33a55ade4b204e84a6c4c681bd751479"  # Replace with actual user ID
    top_artists, top_tracks, top_matches = await get_recommendations(user_id, item_features_matrix_sparse, user_features_matrix_sparse)

    logger.info(f"Top Artists: {top_artists}")
    logger.info(f"Top Tracks: {top_tracks}")
    logger.info(f"Top Matches: {top_matches}")

if __name__ == "__main__":
    asyncio.run(main())
