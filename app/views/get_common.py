from django.http import JsonResponse
from adrf.views import APIView
from app.pagination import StandardResultsSetPagination
from app.db_models.parent_user import ParentUser
import logging

logger = logging.getLogger('app')

async def get_common_items(user, bud_node, item_type):
    user_likes = {}
    bud_likes = {}

    for account in user.associated_accounts.values():
        if account is not None and hasattr(account, 'get_likes'):
            account_likes = await account.get_likes() or {}
            for key, value in account_likes.items():
                if key not in user_likes:
                    user_likes[key] = []
                user_likes[key].extend(value)

    accounts = await bud_node.associated_accounts()
    for account in accounts.values():
        if account is not None and hasattr(account, 'get_likes'):
            account_likes = await account.get_likes() or {}
            for key, value in account_likes.items():
                if key not in bud_likes:
                    bud_likes[key] = []
                bud_likes[key].extend(value)

    if not user_likes or not bud_likes:
        return None

    common_items = user.get_common_items(
        bud_likes.get(item_type, []),
        user_likes.get(item_type, [])
    )

    serialized_items = [
        await item.serialize() if hasattr(item, 'serialize') else item
        for item in common_items
    ]

    return serialized_items

class CommonItemsView(APIView):
    item_type = None

    async def post(self, request):
        return await self.get_common_items(request)

    async def get_common_items(self, request):
        try:
            user = request.user
            bud_id = request.data.get('bud_id')

            if not bud_id:
                return JsonResponse({'error': 'Bud ID not provided'}, status=400)

            bud_node = await ParentUser.nodes.get_or_none(uid=bud_id)

            if user is None or bud_node is None:
                logger.warning(f'User or bud not found: user={user}, bud_id={bud_id}')
                return JsonResponse({'error': 'User or bud not found'}, status=404)

            common_items = await get_common_items(user, bud_node, self.item_type)

            if common_items is None:
                logger.warning('User likes or bud likes returned empty.')
                return JsonResponse({'error': 'No likes found for user or bud.'}, status=404)

            paginator = StandardResultsSetPagination()
            paginated_items = paginator.paginate_queryset(common_items, request)
            response_data = paginator.get_paginated_response(paginated_items)

            logger.info('Successfully fetched common %s data for user=%s, bud_id=%s', self.item_type, user.uid, bud_id)
            return JsonResponse(response_data, safe=False)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error fetching common {self.item_type}: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetCommonLikedArtists(CommonItemsView):
    item_type = 'likes_artists'

    async def post(self, request):
        return await super().get_common_items(request)

class GetCommonLikedTracks(CommonItemsView):
    item_type = 'likes_tracks'

    async def post(self, request):
        return await super().get_common_items(request)
    
class GetCommonLikedGenres(CommonItemsView):
    item_type = 'likes_genres'

    async def post(self, request):
        return await super().get_common_items(request)


class GetCommonLikedAlbums(CommonItemsView):
    item_type = 'likes_albums'

    async def post(self, request):
        return await super().get_common_items(request)

class GetCommonPlayedTracks(CommonItemsView):
    item_type = 'played_tracks'

    async def post(self, request):
        return await super().get_common_items(request)
    
class GetCommonTopArtists(CommonItemsView):
    item_type = 'top_artists'

    async def post(self, request):
        return await super().get_common_items(request)


class GetCommonTopTracks(CommonItemsView):
    item_type = 'top_tracks'
    async def post(self, request):
        return await super().get_common_items(request)

class GetCommonTopGenres(CommonItemsView):
    item_type = 'top_genres'
    async def post(self, request):
        return await super().get_common_items(request)
    
class GetCommonTopAnime(CommonItemsView):
    item_type = 'top_anime'
    async def post(self, request):
        return await super().get_common_items(request)
class GetCommonTopManga(CommonItemsView):
    item_type = 'top_manga'
    async def post(self, request):
        return await super().get_common_items(request)

