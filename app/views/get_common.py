from django.http import JsonResponse
from adrf.views import APIView
from app.pagination import StandardResultsSetPagination
from app.db_models.parent_user import ParentUser
from neomodel import db
import logging
from asgiref.sync import sync_to_async
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger('app')

class CommonItemsMixin:
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super().dispatch(*args, **kwargs)

    async def get_common_items(self, user, bud_node, item_type):
        query = """
        MATCH (user:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_YTMUSIC|CONNECTED_TO_LASTFM|CONNECTED_TO_MAL]->()-[r1]->(item)
        MATCH (bud:ParentUser {uid: $bud_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_YTMUSIC|CONNECTED_TO_LASTFM|CONNECTED_TO_MAL]->()-[r2]->(item)
        WHERE (
            CASE $item_type
                WHEN 'Artist' THEN item:Artist AND type(r1) IN ['LIKES_ARTIST', 'TOP_ARTIST'] AND type(r2) IN ['LIKES_ARTIST', 'TOP_ARTIST']
                WHEN 'Track' THEN item:Track AND type(r1) IN ['LIKES_TRACK', 'TOP_TRACK', 'PLAYED_TRACK'] AND type(r2) IN ['LIKES_TRACK', 'TOP_TRACK', 'PLAYED_TRACK']
                WHEN 'Genre' THEN item:Genre AND type(r1) = 'LIKES_GENRE' AND type(r2) = 'LIKES_GENRE'
                WHEN 'Album' THEN item:Album AND type(r1) = 'LIKES_ALBUM' AND type(r2) = 'LIKES_ALBUM'
                WHEN 'Anime' THEN item:Anime AND type(r1) = 'LIKES_ANIME' AND type(r2) = 'LIKES_ANIME'
                WHEN 'Manga' THEN item:Manga AND type(r1) = 'LIKES_MANGA' AND type(r2) = 'LIKES_MANGA'
                ELSE false
            END
        )
        RETURN DISTINCT item, item.image as image
        """
        params = {
            'user_uid': user.uid,
            'bud_uid': bud_node.uid,
            'item_type': item_type
        }
        
        results, _ = await sync_to_async(db.cypher_query)(query, params)
        
        if not results:
            return None
        
        serialized_items = []
        for item, image in results:
            if hasattr(item, 'serialize'):
                serialized_item = await sync_to_async(item.serialize)()
            else:
                serialized_item = dict(item)
            
            # Add image to the serialized item if available
            if image:
                serialized_item['image'] = image
            
            serialized_items.append(serialized_item)

        return serialized_items

    async def paginate_response(self, request, items):
        paginator = StandardResultsSetPagination()
        paginated_items = paginator.paginate_queryset(items, request)
        response_data = paginator.get_paginated_response(paginated_items)
        return response_data

class CommonItemsView(CommonItemsMixin, APIView):
    item_type = None

    async def post(self, request):
        try:
            user = request.parent_user
            bud_id = request.data.get('bud_id')

            if not bud_id:
                return JsonResponse({'error': 'Bud ID not provided'}, status=400)

            bud_node = await ParentUser.nodes.get_or_none(uid=bud_id)

            if user is None or bud_node is None:
                logger.warning(f'User or bud not found: user={user}, bud_id={bud_id}')
                return JsonResponse({'error': 'User or bud not found'}, status=404)

            common_items = await self.get_common_items(user, bud_node, self.item_type)

            if common_items is None:
                logger.warning('No common items found.')
                return JsonResponse({'error': 'No common items found.'}, status=404)

            response_data = await self.paginate_response(request, common_items)

            logger.info(f'Successfully fetched common {self.item_type} data for user={user.uid}, bud_id={bud_id}')
            return JsonResponse(response_data, safe=False)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error fetching common {self.item_type}: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetCommonLikedArtists(CommonItemsView):
    item_type = 'Artist'

class GetCommonLikedTracks(CommonItemsView):
    item_type = 'Track'
    
class GetCommonLikedGenres(CommonItemsView):
    item_type = 'Genre'

class GetCommonLikedAlbums(CommonItemsView):
    item_type = 'Album'

class GetCommonPlayedTracks(CommonItemsView):
    item_type = 'Track'

class GetCommonTopArtists(CommonItemsView):
    item_type = 'Artist'

class GetCommonTopTracks(CommonItemsView):
    item_type = 'Track'

class GetCommonTopGenres(CommonItemsView):
    item_type = 'Genre'

class GetCommonTopAnime(CommonItemsView):
    item_type = 'Anime'

class GetCommonTopManga(CommonItemsView):
    item_type = 'Manga'

