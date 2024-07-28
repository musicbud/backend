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

            account_ids = [account.uid for account in user.associated_accounts.values() if account]  # Use a list for account UIDs

            # Await the call to get the track node
            track_node = await Track.nodes.get_or_none(uid=track_id)

            if not track_node:
                return JsonResponse({'error': 'Track not found'}, status=404)

            # Get users who liked the specified track, excluding the current user's accounts
            track_users = await track_node.users.exclude(uid__in=account_ids).all()

            buds_data = {}
            unique_bud_uids = set()  # Set to track unique bud UIDs

            for bud in track_users:
                bud_uid = bud.uid
                if bud_uid in unique_bud_uids:
                    continue  # Skip already processed bud

                unique_bud_uids.add(bud_uid)  # Mark this bud as processed

                bud_liked_track_uids = [track.uid for track in await bud.likes_tracks.all()]  # Use list for UIDs
                for account in user.associated_accounts.values():
                    if account:
                        common_tracks = await account.likes_tracks.filter(uid__in=bud_liked_track_uids).all()
                        common_tracks_count = len(common_tracks)

                        # Get the parent and serialize it
                        bud_parent = await bud.parent.all()
                        for parent in bud_parent:
                            parent_uid = parent.uid
                            parent_serialized = await parent.without_relations_serialize()

                            if parent_uid not in buds_data:
                                buds_data[parent_uid] = {
                                    'bud': parent_serialized,
                                    'common_tracks_count': 0,
                                    'common_tracks': []
                                }

                            # Update the aggregated data
                            buds_data[parent_uid]['common_tracks_count'] += common_tracks_count
                            buds_data[parent_uid]['common_tracks'].extend([await track.serialize() for track in common_tracks])

            # Convert the aggregated data to a list
            aggregated_buds_data = list(buds_data.values())

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(aggregated_buds_data, request)

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