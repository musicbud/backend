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

class get_buds_by_top_artists(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_top_artists, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids = {account.uid for account in user_node.associated_accounts.values() if account}
            unique_buds = set()

            # Fetch top artists (placeholder logic)
            top_artists = []  # TODO: Replace with actual logic to get top artists
            logger.debug(f'Fetched top artists: {top_artists}')

            # Fetch users who liked each artist, excluding current user's accounts
            for artist in top_artists:
                if hasattr(artist, 'users'):
                    artist_users = await artist.users.exclude(uid__in=account_ids).all()
                    unique_buds.update(user.uid for user in artist_users if hasattr(user, 'uid'))

            logger.debug(f'Found {len(unique_buds)} unique buds for top artists.')

            # Fetch buds data
            buds_data, total_common_artists_count = await self._fetch_buds_data(user_node, unique_buds)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'total_common_artists_count': total_common_artists_count,
            })

            logger.info(f'Successfully fetched buds by top artists for user: uid={user_node.uid}, total buds fetched: {len(unique_buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByTopArtists: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _fetch_buds_data(self, user_node, unique_buds):
        buds_data = {}
        total_common_artists_count = 0

        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if not bud:
                    logger.warning(f'Bud not found: uid={bud_uid}')
                    continue

                bud_top_artists = await bud.top_artists.all()
                bud_top_artist_uids = {artist.uid for artist in bud_top_artists if hasattr(artist, 'uid')}

                for account in user_node.associated_accounts.values():
                    if account:
                        common_artists = await account.top_artists.filter(uid__in=bud_top_artist_uids).all()
                        common_artists_count = len(common_artists)
                        total_common_artists_count += common_artists_count

                        logger.debug(f'User {user_node.uid} found {common_artists_count} common artists with bud {bud.uid} through account {account.uid}.')

                        bud_parent = await bud.parent.all()
                        for parent in bud_parent:
                            parent_uid = parent.uid
                            parent_serialized = await parent.without_relations_serialize()

                            # Initialize bud data if not already present
                            if parent_uid not in buds_data:
                                buds_data[parent_uid] = {
                                    'parent': parent_serialized,
                                    'commonArtistsCount': 0,
                                    'commonArtists': []
                                }

                            buds_data[parent_uid]['commonArtistsCount'] += common_artists_count
                            buds_data[parent_uid]['commonArtists'].extend(await artist.serialize() for artist in common_artists)

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        # Prepare the list from the dictionary for response
        buds_data_list = [
            {
                'bud': data['parent'],
                'commonArtistsCount': data['commonArtistsCount'],
                'commonArtists': data['commonArtists']
            }
            for data in buds_data.values()
        ]

        logger.debug(f'Prepared buds data list with {len(buds_data_list)} entries.')
        return buds_data_list, total_common_artists_count