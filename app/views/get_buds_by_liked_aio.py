from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..db_models.User import User
from ..db_models.Parent_User import ParentUser
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination
import logging

logger = logging.getLogger('app')

class get_buds_by_liked_aio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_liked_aio, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found in request')
                return JsonResponse({'error': 'User not found'}, status=404)

            logger.info(f'Received request from user: uid={user_node.uid}')

            # Fetch common buds based on liked items from associated accounts
            buds = await self.get_common_buds(user_node)

            # Prepare buds data
            buds_data = await self._fetch_buds_data(buds)

            # Paginate the results
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds for user: uid={user_node.uid}, buds_count={len(buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in get_buds_by_liked_aio: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def get_common_buds(self, user_node):
        """Fetches unique buds based on associated accounts."""
        buds = set()  # Initialize buds as a set to avoid duplicates

        try:
            associated_account_uids = [account.uid for account in user_node.associated_accounts.values() if account]

            for account in user_node.associated_accounts.values():
                if account and hasattr(account, 'get_likes'):
                    user_likes = await account.get_likes()
                    logger.debug(f'User likes for account uid={account.uid}: {len(user_likes)}')

                    if user_likes:
                        await self.find_common_buds(user_likes, user_node.uid, buds)

            # Remove self and associated accounts from buds and ensure uniqueness
            unique_bud_ids = [bud_uid for bud_uid in buds if bud_uid != user_node.uid and bud_uid not in associated_account_uids]
            user_objects = await User.nodes.filter(uid__in=unique_bud_ids).all()

            return user_objects

        except Exception as e:
            logger.error(f'Error in get_common_buds for user uid={user_node.uid}: {e}', exc_info=True)
            return []

    async def find_common_buds(self, user_likes, user_uid, buds):
        """Finds and adds users who liked the same items."""
        liked_artists = user_likes.get('likes_artists', [])
        liked_tracks = user_likes.get('likes_tracks', [])
        liked_genres = user_likes.get('likes_genres', [])
        liked_albums = user_likes.get('likes_albums', [])

        logger.debug(f'Finding common buds for user uid={user_uid}...')

        # Process liked items
        await self._process_liked_items(liked_artists, user_uid, buds, 'artist')
        await self._process_liked_items(liked_tracks, user_uid, buds, 'track')
        await self._process_liked_items(liked_genres, user_uid, buds, 'genre')
        await self._process_liked_items(liked_albums, user_uid, buds, 'album')

        logger.info(f'Total common buds found for user uid={user_uid}: {len(buds)}')

    async def _process_liked_items(self, items, user_uid, buds, item_type):
        """Helper method to process liked items (artists, tracks, genres, albums)."""
        for item in items:
            item_uid = item.uid
            logger.debug(f'Processing {item_type} uid={item_uid}')

            new_buds = await item.users.exclude(uid=user_uid).all()
            buds.update(new_bud.uid for new_bud in new_buds if hasattr(new_bud, 'uid'))
            logger.debug(f'Found {len(new_buds)} new buds from {item_type} uid={item_uid}')

    async def _fetch_buds_data(self, buds):
        """Prepares the data for each bud."""
        buds_data = []

        for bud in buds:
            bud_parent = await bud.parent.all()
            bud_parent_serialized = await self._serialize_parent(bud_parent)

            if not bud_parent_serialized:
                continue  # Skip empty bud data

            buds_data.append({
                'bud': bud_parent_serialized,
            })

        logger.info(f'Data preparation complete. Total buds data prepared: {len(buds_data)}')
        return buds_data

    async def _serialize_parent(self, bud_parent):
        """Serializes the parent data of a bud."""
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data