from datetime import datetime
from urllib.parse import quote
import base64
import os 
import requests
import logging
from .ServiceStrategy import ServiceStrategy

import asyncio

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
        # Generate a code verifier
        self.code_verifier = self.generate_code_verifier()
        self.code_challenge = self.code_verifier  # For plain method, the code_challenge is the same as the code_verifier
        logger.info('MalService initialized successfully.')

    def generate_code_verifier(self):
        # Generate a secure random string for the code verifier
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        logger.debug(f"Generated code_verifier: {code_verifier}")
        return code_verifier

    async def create_authorize_url(self):
        logger.debug('Creating authorize URL')
        authorize_url = (
            f'https://myanimelist.net/v1/oauth2/authorize?client_id={self.client_id}'
            f'&response_type=code&redirect_uri={quote(self.redirect_uri)}&scope={self.scope}'
            f'&code_challenge={self.code_challenge}&code_challenge_method=plain'
        )
        logger.debug(f"Authorize URL: {authorize_url}")
        return authorize_url

    async def get_tokens(self, code):
        logger.debug(f'Getting tokens for code={code}')
        token_url = 'https://myanimelist.net/v1/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,  # Ensure redirect_uri is not encoded again
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
        
        return user_info
    
    async def get_top_anime(self, user, link='https://api.myanimelist.net/v2/users/@me/animelist'):
        logger.debug('Fetching top anime list')
        headers = {'Authorization': f'Bearer {user.access_token}'}

        while link:
            response = requests.get(link, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Failed to fetch top anime list: {response.status_code}')
                break

            top_anime = response.json()
            logger.info('Top anime list fetched successfully.')

            for anime_data in top_anime['data']:
                node = anime_data['node']
                logger.info(f"Anime data: {node}")
                
                # Check if the anime already exists
                anime = await Anime.nodes.get_or_none(anime_id=node['id'])
                if anime:
                    logger.info(f"Anime with ID {node['id']} already exists, skipping creation.")
                    continue

                try:
                    # Create and save the MainPicture node
                    main_picture = await MainPicture(
                        medium=node['main_picture'].get('medium', ''),
                        large=node['main_picture'].get('large', '')
                    ).save()

                    # Create and save the Anime node
                    anime = await Anime(
                        anime_id=node['id'],
                        title=node['title']
                    ).save()

                    # Establish relationships
                    await anime.main_picture.connect(main_picture)
                    await user.top_anime.connect(anime)

                except Exception as e:
                    logger.error(f"Error processing anime {node['id']}: {e}")
                    continue

            # Check for next page link
            link = top_anime.get("paging", {}).get("next")

        return
            


    async def get_top_manga(self, user, link='https://api.myanimelist.net/v2/users/@me/mangalist'):
        logger.debug('Fetching top manga list')
        headers = {'Authorization': f'Bearer {user.access_token}'}

        while link:
            response = requests.get(link, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Failed to fetch top manga list: {response.status_code}')
                break

            top_manga = response.json()
            logger.info('Top manga list fetched successfully.')
            logger.info(f'Top manga list: {top_manga.get("paging", {}).get("next")}')

            for manga_data in top_manga['data']:
                node = manga_data['node']
                logger.info(f"Manga data: {node}")

                # Check if the manga already exists
                manga = await Manga.nodes.get_or_none(manga_id=node['id'])
                if manga:
                    logger.info(f"Manga with ID {node['id']} already exists, skipping creation.")
                    continue

                try:
                    # Create and save the MainPicture node
                    main_picture = await MainPicture(
                        medium=node['main_picture'].get('medium', ''),
                        large=node['main_picture'].get('large', '')
                    ).save()

                    # Create and save the Manga node
                    manga = await Manga(
                        manga_id=node['id'],
                        title=node['title']
                    ).save()

                    # Establish relationships
                    await manga.main_picture.connect(main_picture)
                    await user.top_manga.connect(manga)

                except Exception as e:
                    logger.error(f"Error processing manga {node['id']}: {e}")
                    continue

            # Check for next page link
            link = top_manga.get("paging", {}).get("next")

        return

    async def save_user_likes(self,user):
        try:
            await asyncio.gather(
                self.get_top_anime(user),
                self.get_top_manga(user)
            )
        except Exception as e:
            logger.error(e)
