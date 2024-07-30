from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Track import Track
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class get_buds_by_track(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_track, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user = request.user
            track_id = request.data.get('track_id')

            if not track_id:
                return JsonResponse({'error': 'Track ID not provided'}, status=400)

            account_ids = [account.uid for account in user.associated_accounts.values() if account]  # Use a set for account UIDs

            # Await the call to get the track node
            track_node = await Track.nodes.get_or_none(uid=track_id)

            if not track_node:
                return JsonResponse({'error': 'Track not found'}, status=404)

            # Get users who liked the specified track, excluding the current user's accounts
            track_users = await track_node.users.exclude(uid__in=account_ids).all()

            # Fetch buds data
            buds_data = await self._fetch_buds_data(track_users)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by track for user: uid={user.uid}, track_id={track_id}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByTrack: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, track_users):
        buds_data = []

        try:
            for bud in track_users:
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