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

class get_buds_by_liked_artists(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_liked_artists, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids = [account.uid for account in user_node.associated_accounts.values() if account]
            unique_buds = await self._get_buds_by_liked_artists(user_node, account_ids)

            # Remove self from buds
            unique_buds = [bud for bud in set(unique_buds) if bud not in account_ids]

            buds_data = await self._fetch_buds_data(user_node, unique_buds)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by liked artists for user: uid={user_node.uid}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByLikedArtists: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _get_buds_by_liked_artists(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    liked_artists = await account.likes_artists.all()
                    for artist in liked_artists:
                        artist_users = await artist.users.all()
                        buds.extend([user.uid for user in artist_users if hasattr(user, 'uid')])
        except Exception as e:
            logger.error(f'Error in _get_buds_by_liked_artists: {e}', exc_info=True)
        return buds

    async def _fetch_buds_data(self, user_node, unique_buds):
        buds_data = []

        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if bud:
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