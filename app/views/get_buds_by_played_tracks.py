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

            buds = {}
            account_ids = [account.uid for account in user_node.associated_accounts.values() if account is not None]

            # Fetch played tracks from associated accounts and gather users who played those tracks
            for account in user_node.associated_accounts.values():
                if account and hasattr(account, 'played_tracks'):
                    played_tracks = await account.played_tracks.all()
                    logger.debug(f"User account {account.uid} played tracks: {[track.uid for track in played_tracks]}")
                    for track in played_tracks:
                        track_users = await track.users.exclude(uid__in=account_ids).all()
                        for user in track_users:
                            if user.uid not in account_ids:
                                buds[user.uid] = user

            # Convert buds dictionary values to a list
            buds_list = list(buds.values())
            buds_data = []

            # Fetch common played tracks for each bud
            for bud in buds_list:
                if hasattr(bud, 'played_tracks'):
                    bud_played_tracks = await bud.played_tracks.all()
                    logger.debug(f"Bud {bud.uid} played tracks: {[track.uid for track in bud_played_tracks]}")
                    if not bud_played_tracks:
                        logger.warning(f'Bud {bud.uid} has no played tracks, skipping.')
                        continue  # Skip this bud if they have no played tracks
                    bud_played_track_uids = [track.uid for track in bud_played_tracks]

                    # Find common played tracks between user and bud
                    common_tracks_count = 0
                    common_tracks = []
                    
                    # Iterate through associated accounts to find common tracks
                    for account in user_node.associated_accounts.values():
                        if account and hasattr(account, 'played_tracks'):
                            account_common_tracks = await account.played_tracks.filter(uid__in=bud_played_track_uids).all()
                            common_tracks_count += len(account_common_tracks)
                            common_tracks.extend(account_common_tracks)

                    bud_parent = await bud.parent.all()
                    bud_parent_serialized = [await b.without_relations_serialize() for b in bud_parent]

                    buds_data.append({
                        'bud': bud_parent_serialized,
                        'commonTracksCount': common_tracks_count,
                        'commonTracks': [track.serialize() for track in common_tracks]
                    })
                else:
                    logger.warning(f'Bud {bud.uid} does not have played_tracks attribute.')

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

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