from datetime import datetime
from django.http import JsonResponse
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist
from adrf.views import APIView
from rest_framework.permissions import AllowAny
from app.middlewares.custom_token_auth import CustomTokenAuthentication
from ..db_models.spotify.spotify_user import SpotifyUser
from ..db_models.lastfm.lastfm_user import LastfmUser
from ..db_models.ytmusic.ytmusic_user import YtmusicUser
from ..db_models.mal.mal_user import MalUser

from asgiref.sync import sync_to_async

from ..forms.callback import CodeForm
from app.services.service_selector import get_service_instance
import logging

logger = logging.getLogger(__name__)

class Login(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request):
        service = request.GET.get('service', 'spotify')
        try:
            logger.info(f"Generating authorization link for service: {service}")
            service_instance = get_service_instance(service)
            authorization_link = await service_instance.create_authorize_url()
            logger.info("Generated authorization link successfully")
            return JsonResponse({
                'message': 'Generated authorization link successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': {'authorization_link': authorization_link}
            })
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error generating authorization link: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class YtmusicCallback(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request):
        form = CodeForm(request.GET)

        if form.is_valid():
            code = form.cleaned_data['code']
        
        if not code:
            logger.warning("Authorization code not provided in ytmusic_callback")
            return JsonResponse({'error': 'Authorization code not provided'}, status=400)

        try:
            service = 'ytmusic'
            logger.info("Fetching tokens and user profile for YouTube Music")
            service_instance = get_service_instance(service)

            tokens = await service_instance.get_tokens(code=code)
            user_profile = await service_instance.get_user_profile(tokens)

            try:
                user = await YtmusicUser.nodes.get(channel_handle=user_profile['channelHandle'])
            except MultipleNodesReturned:
                logger.error("Multiple users found with this channel handle")
                return JsonResponse({'error': 'Multiple users found with this channel handle'}, status=500)
            except DoesNotExist:
                logger.info("Creating new YtmusicUser from profile")
                user = await YtmusicUser.create_from_ytmusic_profile(user_profile, tokens)

            updated_user = await YtmusicUser.update_ytmusic_tokens(user, tokens)
            if updated_user is None:
                logger.error("Error updating YTmusic tokens")
                return JsonResponse({'error': 'Error updating tokens'}, status=500)

            logger.info("Logged in successfully to YouTube Music")

            return JsonResponse({
                'message': 'Logged in successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': tokens,
            })
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in ytmusic_callback: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class YtmusicConnect(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    
    async def post(self, request):
        token = request.data.get('ytmusic_token')
        if not token:
            logger.warning("YouTube Music token not provided")
            return JsonResponse({'error': 'YouTube Music token not provided'}, status=400)

        try:
            user = await YtmusicUser.nodes.get_or_none(access_token=token)
            if not user:
                logger.warning("No YouTube Music user found with provided token")
                return JsonResponse({'error': 'No YouTube Music user found with provided token'}, status=404)

            if hasattr(request, 'parent_user') and request.parent_user:
                logger.info("Attaching YtmusicUser to ParentUser")
                await request.parent_user.ytmusic_account.connect(user)
                response_data = {'message': 'YouTube Music user connected to ParentUser successfully.'}
            else:
                response_data = {'message': 'No ParentUser to connect YouTube Music user to.'}

            logger.info(f"Response Data: {response_data}")
            return JsonResponse(response_data, status=200)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in connect_ytmusic: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
        
class SpotifyCallback(APIView):
    permission_classes = [AllowAny]

    async def get(self, request):
        form = CodeForm(request.GET)

        if form.is_valid():
            code = form.cleaned_data['code']
        code = request.GET.get('code')
        if not code:
            logger.warning("Authorization code not provided in spotify_callback")
            return JsonResponse({'error': 'Authorization code not provided'}, status=400)

        try:
            service = 'spotify'
            logger.info("Fetching tokens and user profile for Spotify")
            service_instance = get_service_instance(service)

            tokens = await service_instance.get_tokens(code)
            user_profile = await service_instance.get_user_profile(tokens)

            try:
                user = await SpotifyUser.nodes.get(spotify_id=user_profile['id'])
            except MultipleNodesReturned:
                logger.error("Multiple users found with this Spotify ID")
                return JsonResponse({'error': 'Multiple users found with this Spotify ID'}, status=500)
            except DoesNotExist:
                logger.info("Creating new SpotifyUser from profile")
                user = await SpotifyUser.create_from_spotify_profile(user_profile, tokens)

            updated_user = await SpotifyUser.update_spotify_tokens(user, tokens)
            if updated_user is None:
                logger.error("Error updating Spotify tokens")
                return JsonResponse({'error': 'Error updating tokens'}, status=500)

            logger.info("Logged in successfully to Spotify")        

            return JsonResponse({
                'message': 'Logged in successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': tokens
            })
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in spotify_callback: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class SpotifyConnect(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
            
    async def post(self, request):
        token = request.data.get('spotify_token')
        if not token:
            logger.warning("Spotify token not provided")
            return JsonResponse({'error': 'Spotify token not provided'}, status=400)

        try:
            user = await SpotifyUser.nodes.get_or_none(access_token=token)
            if not user:
                logger.warning("No Spotify user found with provided token")
                return JsonResponse({'error': 'No Spotify user found with provided token'}, status=404)
            if hasattr(request, 'parent_user') and request.parent_user:
                logger.info("Attaching Spotify to ParentUser")
                await request.parent_user.spotify_account.connect(user)
                response_data = {'message': 'Spotify user connected to ParentUser successfully.'}
            else:
                response_data = {'message': 'No ParentUser to connect Spotify user to.'}

            logger.info(f"Response Data: {response_data}")
            return JsonResponse(response_data, status=200)
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in connect_spotify: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class LastfmCallback(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request):
        token = request.GET.get('token')
        if not token:
            logger.warning("Token not provided in lastfm_callback")
            return JsonResponse({'error': 'Token not provided'}, status=400)

        try:
            service = 'lastfm'
            logger.info("Fetching user profile for Last.fm")
            service_instance = get_service_instance(service)
            user_profile = await service_instance.get_user_profile(token)

            try:
                user = await LastfmUser.nodes.get(username=user_profile['username'])
            except MultipleNodesReturned:
                logger.error("Multiple users found with this username")
                return JsonResponse({'error': 'Multiple users found with this username'}, status=500)
            except DoesNotExist:
                logger.info("Creating new LastfmUser from profile")
                user = await LastfmUser.create_from_lastfm_profile(user_profile, token)

            updated_user = await LastfmUser.update_lastfm_tokens(user, token)
            if not updated_user:
                logger.error("Error updating Last.fm user tokens")
                return JsonResponse({'error': 'Error updating user tokens'}, status=500)

            logger.info("Logged in successfully to Last.fm")

            return JsonResponse({
                'message': 'Logged in successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': {'accessToken': token}
            })
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in lastfm_callback: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class LastfmConnect(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
            
    async def post(self, request):
        token = request.data.get('lastfm_token')
        if not token:
                logger.warning("Last.fm token not provided")
                return JsonResponse({'error': 'Last.fm token not provided'}, status=400)

        try:
            user = await LastfmUser.nodes.get_or_none(access_token=token)
            if not user:
                logger.warning("No Last.fm user found with provided token")
                return JsonResponse({'error': 'No Last.fm user found with provided token'}, status=404)
            if hasattr(request, 'parent_user') and request.parent_user:
                logger.info("Attaching Lastfm to ParentUser")
                await request.parent_user.lastfm_account.connect(user)
                response_data = {'message': 'Lastfm user connected to ParentUser successfully.'}
            else:
                response_data = {'message': 'No ParentUser to connect Lastfm user to.'}
            return JsonResponse(response_data, status=200)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in connect_lastfm: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)


class MalCallback(APIView):
    permission_classes = [AllowAny]

    async def get(self, request):
        code = request.GET['code']
        if not code:
            logger.warning("Authorization code not provided in mal_callback")
            return JsonResponse({'error': 'Authorization code not provided'}, status=400)

        try:
            service = 'mal'
            logger.info("Fetching tokens and user profile for MyAnimeList")
            service_instance = get_service_instance(service)

            code_verifier = await sync_to_async(request.session.get)('code_verifier')
            logger.debug(f"Retrieved code_verifier from session: {code_verifier}")  # Add this line
            if not code_verifier:
                logger.error("Code verifier not found in session")
                return JsonResponse({'error': 'Code verifier not found in session'}, status=400)

            tokens = await service_instance.get_tokens(code, code_verifier)
            user_profile = await service_instance.get_user_info(tokens)

            try:
                user = await MalUser.nodes.get(user_id=user_profile['id'])
            except MultipleNodesReturned:
                logger.error("Multiple users found with this MyAnimeList ID")
                return JsonResponse({'error': 'Multiple users found with this MyAnimeList ID'}, status=500)
            except DoesNotExist:
                logger.info("Creating new MalUser from profile")
                user = await MalUser.create_from_mal_profile(user_profile, tokens)
                
            logger.info("Logged in successfully to MyAnimeList")        

            return JsonResponse({
                'message': 'Logged in successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': tokens
            })
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in mal callback: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class MalConnect(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
            
    async def post(self, request):
        token = request.data.get('mal_token')
        if not token:
            logger.warning("MyAnimeList token not provided")
            return JsonResponse({'error': 'MyAnimeList token not provided'}, status=400)

        try:
            user = await MalUser.nodes.get_or_none(access_token=token)
            if not user:
                logger.warning("No MyAnimeList user found with provided token")
                return JsonResponse({'error': 'No MyAnimeList user found with provided token'}, status=404)

            if hasattr(request, 'parent_user') and request.parent_user:
                logger.info("Attaching MyAnimeList to ParentUser")
                await request.parent_user.mal_account.connect(user)
                response_data = {'message': 'MyAnimeList user connected to ParentUser successfully.'}
            else:
                response_data = {'message': 'No ParentUser to connect MyAnimeList user to.'}

            logger.info(f"Response Data: {response_data}")
            return JsonResponse(response_data, status=200)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in mal_connect: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class NotFoundView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request):
        logger.warning("Resource not found on this server")
        return JsonResponse({'error': 'Resource not found on this server'}, status=404)

class ErrorView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request):
        logger.error("Internal Server Error")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
