from .spotify_utils import SpotifyClient
import os

# Define your Spotify application credentials
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
SCOPE = "user-library-read user-read-private user-top-read"

# Initialize the Spotify client
spotify_client = SpotifyClient(client_id=CLIENT_ID,
                               client_secret=CLIENT_SECRET,
                               redirect_uri=REDIRECT_URI,
                               scope=SCOPE)
