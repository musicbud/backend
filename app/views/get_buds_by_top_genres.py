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

            account_ids = [account.uid for account in user_node.associated_accounts.values() if account]
            unique_buds = set()  # Use a set to ensure uniqueness

            # Fetch top genres from associated accounts
            top_genres = []
            for account in user_node.associated_accounts.values():
                if account:
                    if hasattr(account, 'top_genres'):  # Check if account has the top_artists attribute
                        genres = await account.top_genres.all()
                        top_genres.extend(genres)
                    else:
                        logger.warning(f'Account {account.uid} does not have top_genres attribute.')
            logger.debug(f'Fetched top genres: {top_genres}')

            # Fetch users who liked each genre, excluding current user's accounts
            for genre in top_genres:
                if hasattr(genre, 'users'):
                    genre_users = await genre.users.exclude(uid__in=account_ids).all()
                    unique_buds.update(user.uid for user in genre_users if hasattr(user, 'uid'))

            logger.debug(f'Found {len(unique_buds)} unique buds for top genres.')

            # Fetch buds data
            buds_data = await self._fetch_buds_data(unique_buds)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by top genres for user: uid={user_node.uid}, total buds fetched: {len(unique_buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByTopGenres: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, unique_buds):
        buds_data = []

        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if not bud:
                    logger.warning(f'Bud not found: uid={bud_uid}')
                    continue

                bud_parent = await bud.parent.all()
                parent_serialized = await self._serialize_parent(bud_parent)

                buds_data.append({
                    'bud': parent_serialized,
                })

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        logger.debug(f'Prepared buds data list with {len(buds_data)} entries.')
        return buds_data

    async def _serialize_parent(self, bud_parent):
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data