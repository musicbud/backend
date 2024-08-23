import joblib
import numpy as np
import pandas as pd
from lightfm import LightFM

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

# print("User IDs in artist interactions:", list(user_dict_artist.keys()))
# print("User IDs in track interactions:", list(user_dict_track.keys()))
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

# Example usage
sample_recommendation_user_combined(
    model_artist, model_track, interactions_artist, interactions_track,
    user_id='00055176fea33f6e027cd3302289378b', user_dict_artist=user_dict_artist, item_dict_artist=item_dict_artist_reversed,
    user_dict_track=user_dict_track, item_dict_track=item_dict_track_reversed, threshold=0
)
