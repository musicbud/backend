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

            buds_data = await self._fetch_buds_data(buds)

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

    async def _fetch_buds_data(self, buds):
        buds_data = []

        try:
            for bud in buds:
                bud_parent = await bud.parent.all()
                parent_serialized = await self._serialize_parent(bud_parent)

                buds_data.append({
                    'bud': parent_serialized,
                })

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        return buds_data

    async def _serialize_parent(self, bud_parent):
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data