import numpy as np
import joblib
import sys
import os
from dotenv import load_dotenv
from neomodel import config, db
from lightfm import LightFM
from lightfm.data import Dataset
import logging
import asyncio

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

        # Save dictionaries to files
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

    # Create dataset and fit with all items
    dataset = Dataset()
    all_item_names = [track.name for track in tracks] + [artist.name for artist in artists]
    
    # Fit the dataset with users and items
    dataset.fit(
        users=[user.uid for user in users],
        items=all_item_names
    )

    # Map item names to indices
    item_dict = {name: idx for idx, name in enumerate(all_item_names)}
    logger.debug(f"Item Dictionary: {item_dict}")

    interactions = []
    for user in users:
        user_tracks = await user.likes_tracks.all()
        user_artists = await user.likes_artists.all()

        for track in user_tracks:
            track_idx = item_dict.get(track.name)
            if track_idx is not None:
                interactions.append((user.uid, track_idx))
            else:
                logger.warning(f"Track '{track.name}' not found in item dictionary.")

        for artist in user_artists:
            artist_idx = item_dict.get(artist.name)
            if artist_idx is not None:
                interactions.append((user.uid, artist_idx))
            else:
                logger.warning(f"Artist '{artist.name}' not found in item dictionary.")

    logger.debug(f"Interactions: {interactions}")

    # Validate if all item IDs in interactions are in the dictionary
    item_ids_in_dict = set(item_dict.values())
    item_ids_in_interactions = set(item_id for _, item_id in interactions)
    
    missing_item_ids = item_ids_in_interactions - item_ids_in_dict
    if missing_item_ids:
        logger.error(f"Item IDs not found in item dictionary: {missing_item_ids}")

    if not interactions:
        logger.error("No interactions found.")
        return None, None

    try:
        interactions_matrix = dataset.build_interactions(interactions)
        logger.info("Interactions matrix built successfully.")
        
        # Verify item mapping
        num_items = len(dataset.item_features())
        logger.debug(f"Number of items in the matrix: {num_items}")
        logger.debug(f"Sample interaction: {interactions[0] if interactions else 'No interactions available'}")
        
        return interactions_matrix, dataset
    except Exception as e:
        logger.error(f"Error building interactions matrix: {e}")
        return None, None

async def fine_tune_model(model, interactions_matrix, dataset, epochs=10):
    """
    Fine-tunes the existing model with additional interaction data.
    """
    try:
        tracks = await SpotifyTrack.nodes.all()
        artists = await SpotifyArtist.nodes.all()

        track_names = [track.name for track in tracks]
        artist_names = [artist.name for artist in artists]
        all_item_names = track_names + artist_names

        # Ensure the dataset is correctly fitted with all items
        dataset.fit(
            users=[user.uid for user in await SpotifyUser.nodes.all()],
            items=all_item_names
        )

        # Create a mapping from item names to indices
        item_id_to_index = {name: index for index, name in enumerate(all_item_names)}
        logger.debug(f"Item ID to Index Mapping: {item_id_to_index}")

        item_features_data = []
        for track in tracks:
            index = item_id_to_index.get(track.name)
            if index is not None:
                item_features_data.append((index, [1]))  # Example feature: `[1]`
            else:
                logger.warning(f"Track '{track.name}' not found in item ID mapping.")

        for artist in artists:
            index = item_id_to_index.get(artist.name)
            if index is not None:
                item_features_data.append((index, [1]))  # Example feature: `[1]`
            else:
                logger.warning(f"Artist '{artist.name}' not found in item ID mapping.")

        if not item_features_data:
            logger.error("No valid item features data found. Exiting.")
            return

        item_features = dataset.build_item_features(item_features_data)
        logger.info("Item features built successfully.")

        # Check if any IDs in item_features are missing from interactions_matrix
        item_ids_in_features = set(index for index, _ in item_features_data)
        item_ids_in_matrix = set(interactions_matrix.shape[1])  # Assuming the second dimension of matrix is item IDs
        missing_item_ids_in_features = item_ids_in_features - item_ids_in_matrix

        if missing_item_ids_in_features:
            logger.error(f"Item IDs in item features not found in interactions matrix: {missing_item_ids_in_features}")

        model.fit_partial(interactions_matrix, item_features=item_features, epochs=epochs)
        logger.info(f"Model fine-tuned successfully for {epochs} epochs.")
    except Exception as e:
        logger.error(f"Error fine-tuning the model: {e}")

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
    artist_indices = []
    track_indices = []

    for name in liked_artist_names:
        idx = item_dict_artist.get(name)
        if idx is not None:
            artist_indices.append(idx)
        else:
            logger.warning(f"Artist name '{name}' not found in dictionary.")
    
    for name in liked_track_names:
        idx = item_dict_track.get(name)
        if idx is not None:
            track_indices.append(idx)
        else:
            logger.warning(f"Track name '{name}' not found in dictionary.")

    logger.debug(f"Mapped Artist Indices: {artist_indices}")
    logger.debug(f"Mapped Track Indices: {track_indices}")

    return artist_indices, track_indices

async def get_recommendations(user_id):
    logger.info(f"Fetching recommendations for user ID: {user_id}")

    try:
        # Load dictionaries
        item_dict_artist_reversed = joblib.load('item_dict_artist_reversed.pkl')
        item_dict_track_reversed = joblib.load('item_dict_track_reversed.pkl')
        user_dict_artist = joblib.load('user_dict_artist.pkl')
        user_dict_track = joblib.load('user_dict_track.pkl')

        # Ensure dictionaries are loaded correctly
        if None in (item_dict_artist_reversed, item_dict_track_reversed, user_dict_artist, user_dict_track):
            logger.error("One or more dictionaries failed to load.")
            return [], []

        logger.debug(f"Artist Dictionary: {item_dict_artist_reversed}")
        logger.debug(f"Track Dictionary: {item_dict_track_reversed}")

        # Fetch user data
        liked_artist_names, liked_track_names = await get_custom_user_data(user_id)

        # Map names to indices
        artist_indices, track_indices = map_data_to_indices(liked_artist_names, liked_track_names)

        # Compute user embeddings
        user_embedding_artist = np.zeros(model_artist.user_embeddings.shape[1])
        user_embedding_track = np.zeros(model_track.user_embeddings.shape[1])

        if artist_indices and (user_idx_artist := user_dict_artist.get(user_id)) is not None:
            logger.info("Computing artist user embedding...")
            artist_embeddings = []
            for idx in artist_indices:
                if idx in item_dict_artist_reversed:
                    artist_embedding = model_artist.predict(user_idx_artist, idx)
                    if artist_embedding.shape == user_embedding_artist.shape:
                        artist_embeddings.append(artist_embedding)
                    else:
                        logger.warning(f"Inconsistent shape for artist embedding: {artist_embedding.shape}")
            if artist_embeddings:
                user_embedding_artist = np.mean(artist_embeddings, axis=0)

        if track_indices and (user_idx_track := user_dict_track.get(user_id)) is not None:
            logger.info("Computing track user embedding...")
            track_embeddings = []
            for idx in track_indices:
                if idx in item_dict_track_reversed:
                    track_embedding = model_track.predict(user_idx_track, idx)
                    if track_embedding.shape == user_embedding_track.shape:
                        track_embeddings.append(track_embedding)
                    else:
                        logger.warning(f"Inconsistent shape for track embedding: {track_embedding.shape}")
            if track_embeddings:
                user_embedding_track = np.mean(track_embeddings, axis=0)

        # Generate recommendations
        recommendations_artist = np.dot(user_embedding_artist, model_artist.item_embeddings.T) if user_embedding_artist.shape[0] == model_artist.item_embeddings.shape[1] else np.zeros(model_artist.item_embeddings.shape[0])
        recommendations_track = np.dot(user_embedding_track, model_track.item_embeddings.T) if user_embedding_track.shape[0] == model_track.item_embeddings.shape[1] else np.zeros(model_track.item_embeddings.shape[0])

        logger.info("Recommendations generated successfully.")
        return recommendations_artist, recommendations_track
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return [], []

async def main(user_id):
    # Load dictionaries and build the interactions matrix
    await setup_dictionaries()
    interactions_matrix, dataset = await build_interaction_matrix()

    if interactions_matrix is not None:
        # Fine-tune the models
        await fine_tune_model(model_artist, interactions_matrix, dataset, epochs=10)
        await fine_tune_model(model_track, interactions_matrix, dataset, epochs=10)

        # Get recommendations
        recommendations_artist, recommendations_track = await get_recommendations(user_id)

        # Process recommendations as needed
        logger.info(f"Artist Recommendations: {recommendations_artist}")
        logger.info(f"Track Recommendations: {recommendations_track}")

if __name__ == '__main__':
    user_id = '33a55ade4b204e84a6c4c681bd751479'  # Replace with the actual user ID
    asyncio.run(main(user_id))
