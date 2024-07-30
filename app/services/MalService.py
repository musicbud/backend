import datetime
import os
import hashlib
import base64
from urllib.parse import quote
import requests
import logging
from .ServiceStrategy import ServiceStrategy

from ..db_models.mal.List_Status import ListStatus
from ..db_models.mal.Main_Picture import MainPicture
from ..db_models.mal.Mal_User import MalUser
from ..db_models.mal.Mal_Anime import Anime
from ..db_models.mal.Mal_Manga import Manga

logger = logging.getLogger('app')

class MalService(ServiceStrategy):
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        logger.debug('Initializing MalService with client_id=%s', client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        # Generate a code verifier and its corresponding code challenge
        self.code_verifier = self.generate_code_verifier()
        self.code_challenge = self.generate_code_challenge(self.code_verifier)
        logger.info('MalService initialized successfully.')

    def generate_code_verifier(self):
        # Generate a random string for the code verifier
        code_verifier =  base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        code_verifier = 'S1PnqbP_GskeyTyODhYr8kuvFTGjKiI37sjDeq5krxc'
        print(f"code verifier-----   {code_verifier}")

        return code_verifier
    def generate_code_challenge(self, code_verifier):
        print(f"-------------------------code verifier ---------------------\n{code_verifier}")
        # Hash the code verifier and return the base64 URL-safe encoded version
        hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(hashed).rstrip(b'=').decode('utf-8')

    async def create_authorize_url(self):
        logger.debug('Creating authorize URL')
        return (
            f'https://myanimelist.net/v1/oauth2/authorize?client_id={self.client_id}'
            f'&response_type=code&redirect_uri={quote(self.redirect_uri)}&scope={self.scope}'
            f'&code_challenge={self.code_challenge}'
            f'&code_challenge_method=S256'
        )

    async def get_tokens(self, code):
        logger.debug('Getting tokens for code=%s', code)
        print (f" code verifier {self.code_verifier}")
        token_url = 'https://myanimelist.net/v1/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,  # Ensure redirect_uri is not encoded
            'code_verifier': self.code_verifier  # Include the code_verifier here
        }

        # Log the data being sent (sensitive info redacted)
        logger.debug('Requesting tokens with data: %s', {k: v if k != 'client_secret' else 'REDACTED' for k, v in data.items()})

        response = requests.post(token_url, data=data)
        
        # Log the response content for debugging
        logger.debug('Response: %s', response.content)

        try:
            response.raise_for_status()  # Raise an error for bad responses
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error obtaining tokens: {e} - {response.content}")
            raise

        response_data = response.json()
        access_token = response_data.get('access_token')
        logger.info('Access token obtained successfully.')
        return access_token
    
    async def get_user_info(self, access_token):
        logger.debug('Fetching user info')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.myanimelist.net/v2/users/@me', headers=headers)
        user_info = response.json()
        logger.info('MalUser info fetched successfully.')
        anime_statistics = user_info.get('anime_statistics', {})
        user_data = {
            "user_id": user_info['id'],
            "name": user_info['name'],
            "location": user_info.get('location', ''),
            "joined_at": datetime.strptime(user_info['joined_at'], "%Y-%m-%dT%H:%M:%S%z"),
            "num_items_watching": anime_statistics.get('num_items_watching', 0),
            "num_items_completed": anime_statistics.get('num_items_completed', 0),
            "num_items_on_hold": anime_statistics.get('num_items_on_hold', 0),
            "num_items_dropped": anime_statistics.get('num_items_dropped', 0),
            "num_items_plan_to_watch": anime_statistics.get('num_items_plan_to_watch', 0),
            "num_items": anime_statistics.get('num_items', 0),
            "num_days_watched": anime_statistics.get('num_days_watched', 0.0),
            "num_days_watching": anime_statistics.get('num_days_watching', 0.0),
            "num_days_completed": anime_statistics.get('num_days_completed', 0.0),
            "num_days_on_hold": anime_statistics.get('num_days_on_hold', 0.0),
            "num_days_dropped": anime_statistics.get('num_days_dropped', 0.0),
            "num_days": anime_statistics.get('num_days', 0.0),
            "num_episodes": anime_statistics.get('num_episodes', 0),
            "num_times_rewatched": anime_statistics.get('num_times_rewatched', 0),
            "mean_score": anime_statistics.get('mean_score', 0.0)
        }

        user = MalUser(**user_data)
        user.save()
        
        return user_info

    async def get_top_anime(self, access_token):
        logger.debug('Fetching top anime list')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.myanimelist.net/v2/users/@me/animelist?status=completed&sort=list_score&limit=10', headers=headers)
        top_anime = response.json()
        logger.info('Top anime list fetched successfully.')
         
        user_id = top_anime['data'][0]['node']['id']  # Assuming the user ID is in the first item
        user = MalUser.nodes.get(user_id=user_id)

        for anime_data in top_anime['data']:
            node = anime_data['node']
            list_status = anime_data['list_status']
            
            # Create and save the MainPicture node
            main_picture = MainPicture(
                medium=node['main_picture'].get('medium', ''),
                large=node['main_picture'].get('large', '')
            ).save()

            # Create and save the ListStatus node
            list_status_node = ListStatus(
                status=list_status['status'],
                is_rereading=list_status['is_rereading'],
                num_volumes_read=list_status.get('num_volumes_read', 0),
                num_chapters_read=list_status.get('num_chapters_read', 0),
                score=list_status['score'],
                updated_at=datetime.strptime(list_status['updated_at'], "%Y-%m-%dT%H:%M:%S%z")
            ).save()

            # Create and save the Anime node
            anime = Anime(
                anime_id=node['id'],
                title=node['title']
            )
            anime.save()

            # Establish relationships
            anime.main_picture.connect(main_picture)
            anime.list_status.connect(list_status_node)
            user.top_anime.connect(anime)
        
        return top_anime

    async def get_top_manga(self, access_token):
        logger.debug('Fetching top manga list')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.myanimelist.net/v2/users/@me/mangalist?status=completed&sort=list_score&limit=10', headers=headers)
        top_manga = response.json()
        logger.info('Top manga list fetched successfully.')
        
        user_id = top_manga['data'][0]['node']['id']  # Assuming the user ID is in the first item
        user = MalUser.nodes.get(user_id=user_id)

        for manga_data in top_manga['data']:
            node = manga_data['node']
            list_status = manga_data['list_status']
            
            # Create and save the MainPicture node
            main_picture = MainPicture(
                medium=node['main_picture'].get('medium', ''),
                large=node['main_picture'].get('large', '')
            ).save()

            # Create and save the ListStatus node
            list_status_node = ListStatus(
                status=list_status['status'],
                is_rereading=list_status['is_rereading'],
                num_volumes_read=list_status.get('num_volumes_read', 0),
                num_chapters_read=list_status.get('num_chapters_read', 0),
                score=list_status['score'],
                updated_at=datetime.strptime(list_status['updated_at'], "%Y-%m-%dT%H:%M:%S%z")
            ).save()

            # Create and save the Manga node
            manga = Manga(
                manga_id=node['id'],
                title=node['title']
            )
            manga.save()

            # Establish relationships
            manga.main_picture.connect(main_picture)
            manga.list_status.connect(list_status_node)
            user.top_manga.connect(manga)
        
        return top_manga
