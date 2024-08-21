import joblib
import numpy as np
from lightfm import LightFM

from app.db_models import User, Track, Artist

# Load the trained model
model = joblib.load('path/to/your_model.pkl')

async def get_recommendations(user_id):
    user = await User.nodes.get_or_none(uid=user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")

    # Retrieve interactions for the user
    interactions = await get_user_interactions(user)

    # Predict scores for all items
    scores = model.predict(user_id, np.arange(interactions.shape[1]))

    # Get top N recommendations
    top_items = np.argsort(-scores)[:10]  # Adjust the number N as needed

    recommendations = {
        'track_recommendations': await get_top_tracks(top_items),
        'artist_recommendations': await get_top_artists(top_items),
    }
    
    return recommendations

async def get_user_interactions(user):
    # Implement a method to get user interactions from Neo4j
    # This might involve fetching user likes or other interactions
    pass

async def get_top_tracks(top_items):
    # Fetch track details from Neo4j using top_items indices
    tracks = []
    for item_id in top_items:
        track = await Track.nodes.get_or_none(uid=item_id)
        if track:
            tracks.append((track.uid, track.name))
    return tracks

async def get_top_artists(top_items):
    # Fetch artist details from Neo4j using top_items indices
    artists = []
    for item_id in top_items:
        artist = await Artist.nodes.get_or_none(uid=item_id)
        if artist:
            artists.append((artist.uid, artist.name))
    return artists
