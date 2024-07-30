from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Artist import Artist
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class get_buds_by_artist(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_artist, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user = request.user
            artist_id = request.data.get('artist_id')

            if not artist_id:
                return JsonResponse({'error': 'Artist ID not provided'}, status=400)

            account_ids = [account.uid for account in user.associated_accounts.values() if account]

            # Await the call to get the artist node
            artist_node = await Artist.nodes.get_or_none(uid=artist_id)

            if not artist_node:
                return JsonResponse({'error': 'Artist not found'}, status=404)

            # Get users who liked the specified artist, excluding the current user's accounts
            artist_users = await artist_node.users.exclude(uid__in=account_ids).all()

            # Fetch buds data
            buds_data = await self._fetch_buds_data(artist_users)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by artist for user: uid={user.uid}, artist_id={artist_id}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByArtist: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, artist_users):
        buds_data = []

        try:
            for bud in artist_users:
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