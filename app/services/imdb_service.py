import asyncio
from imdb import Cinemagoer
from .service_strategy import ServiceStrategy
from app.db_models.imdb.imdb_movie import ImdbMovie
from app.db_models.imdb.imdb_user import ImdbUser
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ImdbService(ServiceStrategy):
    def __init__(self):
        self.ia = Cinemagoer()
        logger.info("ImdbService initialized")

    async def create_authorize_url(self):
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "read_user_data"
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    async def get_tokens(self, code):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get tokens: {response.text}")
            raise Exception("Failed to get tokens")

    async def refresh_access_token(self, refresh_token):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to refresh token: {response.text}")
            raise Exception("Failed to refresh token")

    async def get_user_profile(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://api.imdb.com/user", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get user profile: {response.text}")
            raise Exception("Failed to get user profile")

    async def fetch_user_movies(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://api.imdb.com/user/watchlist", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch user movies: {response.text}")
            raise Exception("Failed to fetch user movies")

    async def save_user_likes(self, user):
        logger.info(f"Saving user likes for user: {user.username}")
        
        # Clear existing likes
        await user.likes_movies.disconnect_all()

        # Fetch user's favorite movies (in this case, top 50 movies)
        movies = self.ia.get_top250_movies()[:50]  # Using Cinemagoer to get top 50 movies

        for movie in movies:
            node = await ImdbMovie.nodes.get_or_none(imdb_id=movie.movieID)
            if not node:
                # Fetch full movie details
                movie_details = self.ia.get_movie(movie.movieID)
                node = await ImdbMovie(
                    imdb_id=movie.movieID,
                    title=movie['title'],
                    year=movie.get('year'),
                    rating=movie.get('rating'),
                    genres=movie.get('genres', []),
                    plot=movie.get('plot outline', ''),
                    director=movie.get('director', [{}])[0].get('name', '') if movie.get('director') else ''
                ).save()
            
            await user.likes_movies.connect(node)

        logger.info(f"Saved {len(movies)} liked movies for user: {user.username}")

    async def clear_user_likes(self, user):
        logger.info(f"Clearing user likes for user: {user.username}")
        await user.likes_movies.disconnect_all()
        logger.info(f"Cleared likes for user: {user.username}")

    async def sync_user_to_neo4j(self, user_id, username, email=None):
        logger.info(f"Syncing user {username} to Neo4j")
        try:
            user = await self.get_or_create_user(user_id, username, email)
            await self.save_user_likes(user)
            logger.info(f"Successfully synced user {username} to Neo4j")
        except Exception as e:
            logger.error(f"Error syncing user {username} to Neo4j: {e}")
            raise

    async def get_or_create_user(self, user_id, username, email=None):
        user = await ImdbUser.nodes.get_or_none(user_id=user_id)
        if not user:
            user = await ImdbUser(user_id=user_id, username=username, email=email).save()
            logger.info(f"Created new IMDB user: {username}")
        return user