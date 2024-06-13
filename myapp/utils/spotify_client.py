from .spotify_utils import SpotifyClient
import os

# Define your Spotify application credentials
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
scope = "user-library-read user-read-private user-top-read"


# Initialize the Spotify client
spotify_client = SpotifyClient(client_id=CLIENT_ID,
                               client_secret=CLIENT_SECRET,
                               redirect_uri=REDIRECT_URI,
                                scope=scope)
def create_authorize_url():
    return spotify_client.create_authorize_url()


def get_spotify_tokens():
    return spotify_client.get_spotify_tokens()

def get_current_user_profile(access_token):
    return spotify_client.get_current_user_profile(access_token)

def get_user_top_artists_and_tracks(access_token):
        return spotify_client.get_user_top_artists_and_tracks(access_token)
