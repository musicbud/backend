import numpy as np
import pandas as pd
from lightfm import LightFM, cross_validation
from lightfm.evaluation import precision_at_k, auc_score
from scipy.sparse import coo_matrix
import joblib
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Function to create sparse interaction matrix
def create_interaction_matrix_sparse(spotify, user_col, item_col, rating_col, norm=False, threshold=None):
    interactions = spotify.groupby([user_col, item_col])[rating_col].sum().reset_index()
    
    if norm:
        interactions[rating_col] = interactions[rating_col].apply(lambda x: 1 if x > threshold else 0)
    
    # Create user and item dictionaries
    user_dict = create_user_dict(interactions[user_col])
    item_dict = {item: idx for idx, item in enumerate(interactions[item_col].unique())}
    
    users = interactions[user_col].map(user_dict)
    items = interactions[item_col].map(item_dict)
    
    matrix = coo_matrix((interactions[rating_col], (users, items)))
    
    return matrix.tocsr(), user_dict, item_dict

# Function to create user dictionary
def create_user_dict(user_ids):
    unique_user_ids = np.unique(user_ids)
    user_dict = {user_id: idx for idx, user_id in enumerate(unique_user_ids)}
    return user_dict

# Function to create item dictionary
def create_item_dict(df, id_col, name_col):
    item_dict = {}
    for i in range(df.shape[0]):
        item_dict[df[id_col][i]] = df[name_col][i]
    return item_dict

# Function to process data in chunks
def process_data_in_chunks(file_path, chunk_size):
    chunks = pd.read_csv(file_path, chunksize=chunk_size, on_bad_lines='skip')
    full_data = pd.DataFrame()
    
    for chunk in chunks:
        chunk.columns = chunk.columns.str.strip().str.replace('"', '')
        chunk.fillna('Not Specified', inplace=True)
        full_data = pd.concat([full_data, chunk])
    
    return full_data

# Function to sample data
def sample_data(data, fraction):
    return data.sample(frac=fraction, random_state=123)

# Load and process data
file_path = 'spotify_dataset.csv'
chunk_size = 100000  # Adjust based on available memory
fraction = 0.1  # Sample 10% of the data

# Process data in chunks
data = process_data_in_chunks(file_path, chunk_size)

# Sample data
sampled_data = sample_data(data, fraction)

# Clean column names
sampled_data.columns = sampled_data.columns.str.strip().str.replace('"', '')

# Data Preparation
print("Data columns:", sampled_data.columns)
print("Initial data shape:", sampled_data.shape)

# Filtering based on groups of artists who have a track record of more than 50 songs
filtered_data = sampled_data.groupby('artistname').filter(lambda x: len(x) >= 50)
print(filtered_data.shape)
print('After filtering based on the number of songs, there are ', '{0:,}'.format(filtered_data.shape[0]), ' data obtained from ', filtered_data.shape[1], ' variables.')

# Filtering based on users who have played songs by more than 10 artists
filtered_data = filtered_data[filtered_data.groupby('user_id').artistname.transform('nunique') >= 10]
print(filtered_data.shape)
print('After filtering based on the song played by the user, there are ', '{0:,}'.format(filtered_data.shape[0]), ' data obtained from ', filtered_data.shape[1], ' variables.')

# Create frequency dataframe for artists and tracks
spotify_freq_artist = filtered_data.groupby(['user_id', 'artistname']).size().reset_index(name='freq')
spotify_freq_track = filtered_data.groupby(['user_id', 'trackname']).size().reset_index(name='freq')

# Create sparse interaction matrices for artist and track
interactions_artist, user_dict_artist, item_dict_artist = create_interaction_matrix_sparse(
    spotify=spotify_freq_artist, user_col="user_id", item_col='artistname', rating_col='freq', norm=False, threshold=None
)
interactions_track, user_dict_track, item_dict_track = create_interaction_matrix_sparse(
    spotify=spotify_freq_track, user_col="user_id", item_col='trackname', rating_col='freq', norm=False, threshold=None
)

def runMF(interactions, n_components=30, loss='warp', k=15, epoch=30, n_jobs=4):
    model = LightFM(no_components=n_components, loss=loss)
    model.fit(interactions, epochs=epoch, num_threads=n_jobs)
    return model

# Running Model for Artists
model_artist = runMF(interactions=interactions_artist, n_components=30, loss='warp', k=15, epoch=30, n_jobs=4)

# Running Model for Tracks
model_track = runMF(interactions=interactions_track, n_components=30, loss='warp', k=15, epoch=30, n_jobs=4)

# Train-test split
train_artist, test_artist = cross_validation.random_train_test_split(interactions_artist, test_percentage=0.01, random_state=123)
train_track, test_track = cross_validation.random_train_test_split(interactions_track, test_percentage=0.01, random_state=123)

# Evaluate Artist Model
train_auc_artist = auc_score(model_artist, train_artist, num_threads=4).mean()
test_auc_artist = auc_score(model_artist, test_artist, num_threads=4).mean()
train_precision_artist = precision_at_k(model_artist, train_artist, k=10).mean()
test_precision_artist = precision_at_k(model_artist, test_artist, k=10).mean()

print('Artist Model - Train AUC: {:.2f}, Test AUC: {:.2f}, Train Precision: {:.2f}, Test Precision: {:.2f}'.format(
    train_auc_artist, test_auc_artist, train_precision_artist, test_precision_artist))

# Evaluate Track Model
train_auc_track = auc_score(model_track, train_track, num_threads=4).mean()
test_auc_track = auc_score(model_track, test_track, num_threads=4).mean()
train_precision_track = precision_at_k(model_track, train_track, k=10).mean()
test_precision_track = precision_at_k(model_track, test_track, k=10).mean()

print('Track Model - Train AUC: {:.2f}, Test AUC: {:.2f}, Train Precision: {:.2f}, Test Precision: {:.2f}'.format(
    train_auc_track, test_auc_track, train_precision_track, test_precision_track))

# Save the artist model
joblib.dump(model_artist, 'model_artist.pkl')

# Save the track model
joblib.dump(model_track, 'model_track.pkl')

# Save the interaction matrices
joblib.dump(interactions_artist, 'interactions_artist.pkl')
joblib.dump(interactions_track, 'interactions_track.pkl')

# Save the dictionaries
joblib.dump(user_dict_artist, 'user_dict_artist.pkl')
joblib.dump(item_dict_artist, 'item_dict_artist.pkl')
joblib.dump(user_dict_track, 'user_dict_track.pkl')
joblib.dump(item_dict_track, 'item_dict_track.pkl')