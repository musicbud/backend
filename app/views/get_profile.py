from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from ..pagination import StandardResultsSetPagination
from app.db_models.parent_user import ParentUser as Neo4jParentUser
from asgiref.sync import sync_to_async
from app.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status       
import logging
import traceback
from pprint import pformat
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('app')

class GetItemsMixin(APIView):
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]
    item_type = None
    item_attribute = None

    async def post(self, request):
        try:
            neo4j_user = request.user  # The user should already be authenticated and set on the request

            logger.debug(f"User object type: {type(request.user)}")
            logger.debug(f"User object attributes: {dir(request.user)}")

            if not neo4j_user:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            items = []
            account_types = ['spotify_account', 'lastfm_account', 'ytmusic_account', 'mal_account', 'imdb_account']
            
            for account_type in account_types:
                account_relationship = getattr(neo4j_user, account_type, None)
                if account_relationship:
                    account = await account_relationship.single()
                    if account:
                        items_method = getattr(account, self.item_attribute, None)
                        if items_method:
                            account_items = await items_method.all()
                            items.extend(account_items)

            logger.debug(f"Fetched items: {pformat(items)}")

            serialized_items = []
            for item in items:
                logger.debug(f"Processing item: {pformat(item)}")
                logger.debug(f"Item type: {type(item)}")
                logger.debug(f"Item attributes: {dir(item)}")
                if isinstance(item, dict):
                    serialized_items.append(item)
                elif hasattr(item, 'serialize'):
                    serialized_item = await sync_to_async(item.serialize)()
                    serialized_items.append(serialized_item)
                else:
                    logger.warning(f"Item {item} is not a dict and does not have a serialize method")

            paginator = StandardResultsSetPagination()
            paginated_items = await sync_to_async(paginator.paginate_queryset)(serialized_items, request)

            paginated_response = await sync_to_async(paginator.get_paginated_response)(paginated_items)
            paginated_response.update({
                'message': f'Fetched {self.item_type.replace("_", " ")} successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched {self.item_type.replace("_", " ")} for user: uid={neo4j_user.uid}')
            return JsonResponse(paginated_response, safe=False)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error fetching {self.item_type}: {e}')
            logger.error(traceback.format_exc())
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetTopArtists(GetItemsMixin):
    item_type = 'top_artists'
    item_attribute = 'top_artists'

class GetTopTracks(GetItemsMixin):
    item_type = 'top_tracks'
    item_attribute = 'top_tracks'

class GetTopGenres(GetItemsMixin):
    item_type = 'top_genres'
    item_attribute = 'top_genres'

class GetLikedTracks(GetItemsMixin):
    item_type = 'liked_tracks'
    item_attribute = 'likes_tracks'

class GetLikedArtists(GetItemsMixin):
    item_type = 'liked_artists'
    item_attribute = 'likes_artists'

class GetLikedGenres(GetItemsMixin):
    item_type = 'liked_genres'
    item_attribute = 'likes_genres'

class GetLikedAlbums(GetItemsMixin):
    item_type = 'liked_albums'
    item_attribute = 'liked_albums'

class GetPlayedTracks(GetItemsMixin):
    item_type = 'played_tracks'
    item_attribute = 'played_tracks'

class GetTopAnime(GetItemsMixin):
    item_type = 'top_anime'
    item_attribute = 'top_anime'

class GetTopManga(GetItemsMixin):
    item_type = 'top_manga'
    item_attribute = 'top_manga'

class AsyncAPIView(APIView):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        async def async_view(*args, **kwargs):
            return await sync_to_async(view)(*args, **kwargs)
        return async_view

    async def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers

        try:
            await self.initial(request, *args, **kwargs)
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = await handler(request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    async def initial(self, request, *args, **kwargs):
        await sync_to_async(super().initial)(request, *args, **kwargs)

class AsyncIsAuthenticated(IsAuthenticated):
    async def has_permission(self, request, view):
        return await sync_to_async(super().has_permission)(request, view)
@method_decorator(csrf_exempt, name='dispatch')
class GetProfile(View):
    def get(self, request):
        logger.info("GetProfile: Entering GET method")
        response_data = {"message": "This is a test response"}
        logger.info("GetProfile: Exiting GET method")
        return JsonResponse(response_data)

    def post(self, request):
        logger.info("GetProfile: Entering POST method")
        response_data = {"message": "This is a test response for POST"}
        logger.info("GetProfile: Exiting POST method")
        return JsonResponse(response_data)

