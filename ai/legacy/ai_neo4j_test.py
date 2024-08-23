import numpy as np
import joblib
import sys
import os
from dotenv import load_dotenv
from neomodel import config, db
from lightfm import LightFM
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Set up the database connection
config.DATABASE_URL = os.getenv('NEOMODEL_NEO4J_BOLT_URL')
db.set_connection(config.DATABASE_URL)

# Add the project directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db_models.spotify.spotify_user import SpotifyUser
from app.db_models.spotify.spotify_artist import SpotifyArtist
from app.db_models.spotify.spotify_track import SpotifyTrack
from app.db_models.track import Track
from app.db_models.artist import Artist

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

# Function to get custom user data
async def get_custom_user_data(user_id):
    try:
        user = await SpotifyUser.nodes.get(uid=user_id)
        liked_artists = await user.likes_artists.all()
        liked_tracks = await user.likes_tracks.all()

        liked_artist_names = [artist.name.strip() for artist in liked_artists]
        liked_track_names = [track.name.strip() for track in liked_tracks]

        return liked_artist_names, liked_track_names
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        return [], []

# Map data to indices
def map_data_to_indices(liked_artist_names, liked_track_names):
    artist_indices = [item_dict_artist.get(name) for name in liked_artist_names if name in item_dict_artist]
    track_indices = [item_dict_track.get(name) for name in liked_track_names if name in item_dict_track]

    return artist_indices, track_indices

# Get recommendations
async def get_recommendations(user_id):
    logger.info(f"Fetching recommendations for user ID: {user_id}")

    try:
        liked_artist_names, liked_track_names = await get_custom_user_data(user_id)
        artist_indices, track_indices = map_data_to_indices(liked_artist_names, liked_track_names)

        # Load user dictionaries
        try:
            user_dict_artist = joblib.load('user_dict_artist.pkl')
            user_dict_track = joblib.load('user_dict_track.pkl')
        except Exception as e:
            logger.error(f"Error loading user dictionaries: {e}")
            return [], []

        # Verify if user indices exist
        user_idx_artist = user_dict_artist.get(user_id)
        user_idx_track = user_dict_track.get(user_id)

        if user_idx_artist is None:
            logger.warning("User index for artist is None.")
        if user_idx_track is None:
            logger.warning("User index for track is None.")

        # Compute embeddings
        if user_idx_artist is None and artist_indices:
            logger.info("Computing artist user embedding...")
            predictions = model_artist.predict(np.zeros(len(artist_indices)), artist_indices)
            logger.debug(f"Predictions for artists: {predictions}")
            user_embedding = np.mean(predictions, axis=0)
        else:
            user_embedding = model_artist.get_user_representations()[1][user_idx_artist]

        if user_idx_track is None and track_indices:
            logger.info("Computing track user embedding...")
            predictions = model_track.predict(np.zeros(len(track_indices)), track_indices)
            logger.debug(f"Predictions for tracks: {predictions}")
            track_embedding = np.mean(predictions, axis=0)
        else:
            track_embedding = model_track.get_user_representations()[1][user_idx_track]

        logger.debug(f"User Embedding (Artist): {user_embedding}")
        logger.debug(f"Track Embedding: {track_embedding}")

        # Compute scores
        artist_scores = np.dot(user_embedding, model_artist.get_item_representations()[1].T).flatten()
        track_scores = np.dot(track_embedding, model_track.get_item_representations()[1].T).flatten()

        logger.debug(f"Artist Scores Shape: {artist_scores.shape}")
        logger.debug(f"Track Scores Shape: {track_scores.shape}")

        # Ensure top indices are correctly extracted
        top_artists = np.argsort(artist_scores)[-10:][::-1]
        top_tracks = np.argsort(track_scores)[-10:][::-1]

        logger.debug(f"Top Artists Indices: {top_artists}")
        logger.debug(f"Top Tracks Indices: {top_tracks}")

        # Verify if indices are within the mapping range
        logger.debug(f"Max Artist Index in Dictionary: {max(item_dict_artist.values())}")
        logger.debug(f"Max Track Index in Dictionary: {max(item_dict_track.values())}")

        # Check if indices are in the mapping dictionaries
        missing_artists = [idx for idx in top_artists if idx not in item_dict_artist_reversed]
        missing_tracks = [idx for idx in top_tracks if idx not in item_dict_track_reversed]

        if missing_artists:
            logger.warning(f"Missing Artist Indices: {missing_artists}")
        if missing_tracks:
            logger.warning(f"Missing Track Indices: {missing_tracks}")

        # Map indices to names or default data
        recommended_artists = [item_dict_artist_reversed.get(idx, f"Artist ID {idx}") for idx in top_artists]
        recommended_tracks = [item_dict_track_reversed.get(idx, f"Track ID {idx}") for idx in top_tracks]

        # Exclude already liked items from recommendations
        recommended_artists = [artist for artist in recommended_artists if artist not in liked_artist_names]
        recommended_tracks = [track for track in recommended_tracks if track not in liked_track_names]

        logger.info(f"Recommended Artists: {recommended_artists}")
        logger.info(f"Recommended Tracks: {recommended_tracks}")

        return recommended_artists, recommended_tracks

    except Exception as e:
        logger.error(f"Error during recommendation process: {e}")
        return [], []

# Main async function
async def main():
    global item_dict_artist, item_dict_artist_reversed
    global item_dict_track, item_dict_track_reversed
    global user_dict_artist, user_dict_track

    # Setup dictionaries
    await setup_dictionaries()

    # Example user ID
    user_id = '33a55ade4b204e84a6c4c681bd751479'  # Replace with a valid user ID from your Neo4j database

    # Run the recommendation process
    recommendations = await get_recommendations(user_id)
    print("Recommended Artists:", recommendations[0])
    print("Recommended Tracks:", recommendations[1])

# Run the main function in the event loop
if __name__ == "__main__":
    asyncio.run(main())
