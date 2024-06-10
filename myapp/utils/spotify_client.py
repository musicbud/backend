from .spotify_utils import SpotifyClient

# Define your Spotify application credentials
CLIENT_ID = "cd3fb6fd6379457bacc7f3559ba36c13"
CLIENT_SECRET = "ff3d663125f8429a9fe64836f8016eef"
REDIRECT_URI = "http://localhost:8000/callback"
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



