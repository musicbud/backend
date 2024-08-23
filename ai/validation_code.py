import numpy as np
import joblib
import warnings
from scipy.sparse import coo_matrix
from lightfm import LightFM

warnings.simplefilter(action='ignore', category=FutureWarning)

# Example of user features for testing
user_features = [
    ('00055176fea33f6e027cd3302289378b', [0.1, 0.2, 0.3]),
    ('0007f3dd09c91198371454c608d47f22', [0.4, 0.5, 0.6]),
    ('000c11a16c89aa4b14b328080f5954ee', [0.7, 0.8, 0.9]),
]

# Load the saved user to index mapping
user_id_to_index = joblib.load('user_id_to_index.pkl')

# Verify contents
print("User ID to Index Mapping:", user_id_to_index)

# Debugging - Print all user features
print("User Features Provided:", user_features)

# Convert user features to indexed format
user_features_indexed = [
    (user_id_to_index[uid], feature_vector)
    for uid, feature_vector in user_features
    if uid in user_id_to_index
]

# Check if user_features_indexed is not empty
if not user_features_indexed:
    raise ValueError("No valid user features to train on.")

print("User Features Indexed:", user_features_indexed)

# Example function to build user features matrix
def build_user_features_matrix(user_features_indexed, n_features):
    user_ids = [uid for uid, _ in user_features_indexed]
    feature_matrix = np.zeros((len(user_ids), n_features))
    
    user_id_index = {uid: idx for idx, uid in enumerate(user_ids)}
    
    for uid, features in user_features_indexed:
        idx = user_id_index[uid]
        feature_matrix[idx, :] = features
    
    return feature_matrix

# Example feature size (you should match this with the actual number of features)
n_features = len(user_features[0][1])

# Build user features matrix
user_features_matrix = build_user_features_matrix(user_features_indexed, n_features)

# Convert user features matrix to a sparse matrix
user_features_sparse = coo_matrix(user_features_matrix)

# Example of how you might use the LightFM model
# For demonstration, assuming user_features_sparse is for content-based recommendation.
model = LightFM(no_components=30, loss='warp')

# Fit the model using the sparse matrix
model.fit(user_features_sparse, epochs=30, num_threads=4)

# Save the model
joblib.dump(model, 'model.pkl')

print("Model training complete and saved.")
