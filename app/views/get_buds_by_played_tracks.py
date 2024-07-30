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

class get_buds_by_played_tracks(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_played_tracks, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            # Collect valid account UIDs
            account_ids = [account.uid for account in user_node.associated_accounts.values() if account]

            # Fetch buds who played tracks liked by the user
            buds = await self._get_buds_by_played_tracks(user_node, account_ids)

            # Prepare buds data
            buds_data = await self._serialize_buds_data(buds)

            # Paginate response
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            # Create paginated response
            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by played tracks for user: uid={user_node.uid}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByPlayedTracks: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _get_buds_by_played_tracks(self, user_node, account_ids):
        buds = {}

        for account in user_node.associated_accounts.values():
            if account and hasattr(account, 'played_tracks'):
                played_tracks = await account.played_tracks.all()
                for track in played_tracks:
                    # Fetch users who played the track, excluding the current user's accounts
                    track_users = await track.users.exclude(uid__in=account_ids).all()
                    for user in track_users:
                        if user.uid not in account_ids:
                            buds[user.uid] = user

        return buds

    async def _serialize_buds_data(self, buds):
        buds_data = []

        for bud in buds.values():
            if hasattr(bud, 'parent'):
                bud_parent = await bud.parent.all()
                bud_parent_serialized = [await b.without_relations_serialize() for b in bud_parent]

                buds_data.append({
                    'bud': bud_parent_serialized,
                })
            else:
                logger.warning(f'Bud {bud.uid} does not have a parent attribute.')

        return buds_data