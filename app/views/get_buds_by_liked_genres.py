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

class get_buds_by_liked_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_liked_genres, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids, liked_genres = await self._get_account_liked_genres(user_node)

            buds = await self._get_buds_by_liked_genres(liked_genres, account_ids)

            buds_data, total_common_genres_count = await self._fetch_buds_data(user_node, buds, account_ids)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by liked genres for user: uid={user_node.uid}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByLikedGenres: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _get_account_liked_genres(self, user_node):
        account_ids = []
        liked_genres = []

        try:
            for account in user_node.associated_accounts.values():
                if account:
                    if hasattr(account, 'likes_genres'):
                        account_liked_genres = await account.likes_genres.all()
                    else:
                        account_liked_genres = []
                    
                    liked_genres.extend(account_liked_genres)
                    account_ids.append(account.uid)
        except Exception as e:
            logger.error(f'Error in _get_account_liked_genres: {e}', exc_info=True)

        return account_ids, liked_genres

    async def _get_buds_by_liked_genres(self, liked_genres, account_ids):
        buds = set()

        try:
            for genre in liked_genres:
                genre_users = await genre.users.exclude(uid__in=account_ids).all()
                buds.update(genre_users)
        except Exception as e:
            logger.error(f'Error in _get_buds_by_liked_genres: {e}', exc_info=True)

        return buds

    async def _fetch_buds_data(self, user_node, buds, account_ids):
        buds_data = {}
        total_common_genres_count = 0

        try:
            for bud in buds:
                try:
                    bud_liked_genres = await bud.likes_genres.all()
                    bud_liked_genre_uids = [genre.uid for genre in bud_liked_genres]

                    common_genres = await user_node.likes_genres.filter(uid__in=bud_liked_genre_uids).all()
                    common_genres_count = len(common_genres)
                    total_common_genres_count += common_genres_count

                    bud_parent = await bud.parent.all()
                    for parent in bud_parent:
                        parent_uid = parent.uid
                        parent_serialized = await parent.without_relations_serialize()
                        if parent_uid not in buds_data:
                            buds_data[parent_uid] = {
                                'parent': parent_serialized,
                                'commonGenresCount': 0,
                                'commonGenres': []
                            }
                        buds_data[parent_uid]['commonGenresCount'] += common_genres_count
                        buds_data[parent_uid]['commonGenres'].extend([await genre.serialize() for genre in common_genres])

                except Exception as e:
                    logger.error(f'Error processing bud: uid={bud.uid} - {e}', exc_info=True)
        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        buds_data_list = [
            {
                'bud': data['parent'],
                'commonGenresCount': data['commonGenresCount'],
                'commonGenres': data['commonGenres']
            }
            for data in buds_data.values()
        ]

        return buds_data_list, total_common_genres_count