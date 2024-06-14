from .spotify_client import spotify_client

def create_authorize_url():
    return spotify_client.create_authorize_url()

def get_spotify_tokens(code):
    return spotify_client.get_spotify_tokens(code)

def get_current_user_profile(access_token):
    return spotify_client.get_current_user_profile(access_token)

def get_user_top_artists_and_tracks(access_token, time_range='long_term', limit=50):
    return spotify_client.get_user_top_artists_and_tracks(access_token, time_range, limit)

def fetch_common_artists_tracks_and_genres(access_token, artist_ids, track_ids,genres_ids):
    return spotify_client.fetch_common_artists_tracks_and_genres(access_token, artist_ids, track_ids,genres_ids)

def fetch_artists(access_token, artist_ids):
    return spotify_client._fetch_artists(spotify_client.sp, artist_ids)

def fetch_tracks(access_token, track_ids):
    return spotify_client._fetch_tracks(spotify_client.sp, track_ids)
def fetch_genres(access_token, genre_ids):
    return spotify_client._fetch_genres(spotify_client.sp, genre_ids)
