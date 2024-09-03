from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging
import traceback
from pprint import pformat

logger = logging.getLogger('app')

class GetItemsMixin(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    item_type = None
    item_attribute = None

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            items = []
            for account in user_node.associated_accounts.values():
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
                    serialized_item = await item.serialize()  # Remove await here
                    serialized_items.append(serialized_item)
                else:
                    logger.warning(f"Item {item} is not a dict and does not have a serialize method")

            paginator = StandardResultsSetPagination()
            paginated_items = paginator.paginate_queryset(serialized_items, request)

            paginated_response = paginator.get_paginated_response(paginated_items)
            paginated_response.update({
                'message': f'Fetched {self.item_type.replace("_", " ")} successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched {self.item_type.replace("_", " ")} for user: uid={user_node.uid}')
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
