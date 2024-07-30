from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Genre import Genre
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class get_buds_by_genre(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_genre, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user = request.user
            genre_id = request.data.get('genre_id')

            if not genre_id:
                return JsonResponse({'error': 'Genre ID not provided'}, status=400)

            account_ids = [account.uid for account in user.associated_accounts.values() if account]
            # Await the call to get the genre node
            genre_node = await Genre.nodes.get_or_none(uid=genre_id)

            if not genre_node:
                return JsonResponse({'error': 'Genre not found'}, status=404)

            # Get users who liked the specified genre, excluding the current user's accounts
            genre_users = await genre_node.users.exclude(uid__in=account_ids).all()

            # Fetch buds data
            buds_data = await self._fetch_buds_data(genre_users)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by genre for user: uid={user.uid}, genre_id={genre_id}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByGenre: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, genre_users):
        buds_data = []

        try:
            for bud in genre_users:
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