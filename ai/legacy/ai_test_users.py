import joblib
import numpy as np
import pandas as pd
from lightfm import LightFM
from scipy.spatial.distance import cosine

# Load the saved models
model_artist = joblib.load('model_artist.pkl')
model_track = joblib.load('model_track.pkl')

# Load the interaction matrices
interactions_artist = joblib.load('interactions_artist.pkl')
interactions_track = joblib.load('interactions_track.pkl')

# Load the dictionaries
user_dict_artist = joblib.load('user_dict_artist.pkl')
item_dict_artist = joblib.load('item_dict_artist.pkl')
user_dict_track = joblib.load('user_dict_track.pkl')
item_dict_track = joblib.load('item_dict_track.pkl')

item_dict_artist_reversed = {v: k for k, v in item_dict_artist.items()}
item_dict_track_reversed = {v: k for k, v in item_dict_track.items()}

def get_user_vector(model, interactions, user_id):
    user_x = user_dict_artist.get(user_id, None)
    if user_x is not None:
        scores = model.predict(user_x, np.arange(interactions.shape[1]))
        return scores
    return None

def find_similar_users(user_id, model_artist, model_track, interactions_artist, interactions_track, user_dict_artist, user_dict_track, nrec_users=5):
    user_vector_artist = get_user_vector(model_artist, interactions_artist, user_id)
    user_vector_track = get_user_vector(model_track, interactions_track, user_id)
    
    if user_vector_artist is None or user_vector_track is None:
        print("User ID not found in one or both of the interaction matrices.")
        return
    
    user_similarities = []
    
    for other_user_id in user_dict_artist.keys():
        if other_user_id == user_id:
            continue
        
        other_user_vector_artist = get_user_vector(model_artist, interactions_artist, other_user_id)
        other_user_vector_track = get_user_vector(model_track, interactions_track, other_user_id)
        
        if other_user_vector_artist is None or other_user_vector_track is None:
            continue
        
        similarity_artist = 1 - cosine(user_vector_artist, other_user_vector_artist)
        similarity_track = 1 - cosine(user_vector_track, other_user_vector_track)
        
        # Combine similarities from artist and track vectors
        combined_similarity = (similarity_artist + similarity_track) / 2
        user_similarities.append((other_user_id, combined_similarity))
    
    user_similarities = sorted(user_similarities, key=lambda x: x[1], reverse=True)
    
    return user_similarities[:nrec_users]

def sample_recommendation_user_combined(model_artist, model_track, interactions_artist, interactions_track,
                                        user_id, user_dict_artist, item_dict_artist, user_dict_track,
                                        item_dict_track, threshold=0, nrec_items=10, show=True):
    user_x_artist = user_dict_artist.get(user_id, None)
    user_x_track = user_dict_track.get(user_id, None)
    
    if user_x_artist is None or user_x_track is None:
        print("User ID not found in one or both of the interaction matrices.")
        return
    
    # Predict scores
    scores_artist = pd.Series(model_artist.predict(user_x_artist, np.arange(interactions_artist.shape[1])))
    scores_track = pd.Series(model_track.predict(user_x_track, np.arange(interactions_track.shape[1])))
    
    # Sort and get top recommendations
    scores_artist = scores_artist.sort_values(ascending=False).index[:nrec_items]
    scores_track = scores_track.sort_values(ascending=False).index[:nrec_items]
    
    # Get known items
    known_items_artist = list(np.where(interactions_artist[user_x_artist].toarray()[0] > 0)[0])
    known_items_track = list(np.where(interactions_track[user_x_track].toarray()[0] > 0)[0])
    
    # Map IDs to names using reversed dictionaries
    known_items_artist_names = [item_dict_artist.get(i, f"Unknown Artist {i}") for i in known_items_artist]
    known_items_track_names = [item_dict_track.get(i, f"Unknown Track {i}") for i in known_items_track]
    
    recommended_artist_names = [item_dict_artist.get(i, f"Unknown Artist {i}") for i in scores_artist if i not in known_items_artist]
    recommended_track_names = [item_dict_track.get(i, f"Unknown Track {i}") for i in scores_track if i not in known_items_track]
    
    if show:
        print("Known Likes - Artists:")
        for i, artist in enumerate(known_items_artist_names, 1):
            print(f"{i}- {artist}")
        
        print("\nRecommended Artists:")
        for i, artist in enumerate(recommended_artist_names, 1):
            print(f"{i}- {artist}")
        
        print("\nKnown Likes - Tracks:")
        for i, track in enumerate(known_items_track_names, 1):
            print(f"{i}- {track}")
        
        print("\nRecommended Tracks:")
        for i, track in enumerate(recommended_track_names, 1):
            print(f"{i}- {track}")
    
    # Recommend similar users
    similar_users = find_similar_users(user_id, model_artist, model_track, interactions_artist, interactions_track, user_dict_artist, user_dict_track)
    
    if similar_users:
        print("\nRecommended Users:")
        for i, (other_user_id, similarity) in enumerate(similar_users, 1):
            print(f"{i}- User ID: {other_user_id}, Similarity: {similarity:.4f}")

# Example usage
sample_recommendation_user_combined(
    model_artist, model_track, interactions_artist, interactions_track,
    user_id='00055176fea33f6e027cd3302289378b', user_dict_artist=user_dict_artist, item_dict_artist=item_dict_artist_reversed,
    user_dict_track=user_dict_track, item_dict_track=item_dict_track_reversed, threshold=0
)
