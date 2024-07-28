from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class get_buds_by_top_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_top_genres, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids = {account.uid for account in user_node.associated_accounts.values() if account}
            unique_buds = set()  # Use a set to ensure uniqueness

            # Fetch top genres (placeholder logic)
            top_genres = []  # TODO: Replace with actual logic to get top genres
            logger.debug(f'Fetched top genres: {top_genres}')

            # Fetch users who liked each genre, excluding current user's accounts
            for genre in top_genres:
                if hasattr(genre, 'users'):
                    genre_users = await genre.users.exclude(uid__in=account_ids).all()
                    unique_buds.update(user.uid for user in genre_users if hasattr(user, 'uid'))

            logger.debug(f'Found {len(unique_buds)} unique buds for top genres.')

            # Fetch buds data
            buds_data, total_common_genres_count = await self._fetch_buds_data(user_node, unique_buds)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'total_common_genres_count': total_common_genres_count,
            })

            logger.info(f'Successfully fetched buds by top genres for user: uid={user_node.uid}, total buds fetched: {len(unique_buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByTopGenres: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, user_node, unique_buds):
        buds_data = {}
        total_common_genres_count = 0

        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if not bud:
                    logger.warning(f'Bud not found: uid={bud_uid}')
                    continue

                bud_top_genres = await bud.top_genres.all()
                bud_top_genre_uids = {genre.uid for genre in bud_top_genres if hasattr(genre, 'uid')}

                for account in user_node.associated_accounts.values():
                    if account:
                        common_genres = await account.top_genres.filter(uid__in=bud_top_genre_uids).all()
                        common_genres_count = len(common_genres)
                        total_common_genres_count += common_genres_count

                        logger.debug(f'User {user_node.uid} found {common_genres_count} common genres with bud {bud.uid} through account {account.uid}.')

                        bud_parent = await bud.parent.all()
                        for parent in bud_parent:
                            parent_uid = parent.uid
                            parent_serialized = await parent.without_relations_serialize()

                            # Initialize bud data if not already present
                            if parent_uid not in buds_data:
                                buds_data[parent_uid] = {
                                    'parent': parent_serialized,
                                    'commonGenresCount': 0,
                                    'commonGenres': []
                                }

                            buds_data[parent_uid]['commonGenresCount'] += common_genres_count
                            buds_data[parent_uid]['commonGenres'].extend(await genre.serialize() for genre in common_genres)

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        # Prepare the list from the dictionary for response
        buds_data_list = [
            {
                'bud': data['parent'],
                'commonGenresCount': data['commonGenresCount'],
                'commonGenres': data['commonGenres']
            }
            for data in buds_data.values()
        ]

        logger.debug(f'Prepared buds data list with {len(buds_data_list)} entries.')
        return buds_data_list, total_common_genres_count