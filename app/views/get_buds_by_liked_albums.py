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

class get_buds_by_liked_albums(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_liked_albums, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids = {account.uid for account in user_node.associated_accounts.values() if account}
            buds = await self._get_buds_by_liked_albums(user_node, account_ids)

            # Remove self from buds
            unique_buds = [bud for bud in set(buds) if bud not in account_ids]

            buds_data, total_common_albums_count = await self._fetch_buds_data(user_node, unique_buds)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by liked albums for user: uid={user_node.uid}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByLikedAlbums: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def _get_buds_by_liked_albums(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    liked_albums = await account.likes_albums.all()
                    for album in liked_albums:
                        album_users = await album.users.all()
                        buds.extend([user.uid for user in album_users if hasattr(user, 'uid')])
        except Exception as e:
            logger.error(f'Error in _get_buds_by_liked_albums: {e}', exc_info=True)
        return buds

    async def _fetch_buds_data(self, user_node, unique_buds):
        buds_data = {}
        total_common_albums_count = 0

        try:
            for bud_uid in unique_buds:
                try:
                    bud = await User.nodes.get_or_none(uid=bud_uid)
                    if bud:
                        bud_liked_albums = await bud.likes_albums.all()
                        bud_liked_album_uids = [album.uid for album in bud_liked_albums]

                        for account in user_node.associated_accounts.values():
                            if account:
                                common_albums = await account.likes_albums.filter(uid__in=bud_liked_album_uids).all()
                                common_albums_count = len(common_albums)
                                total_common_albums_count += common_albums_count

                                bud_parent = await bud.parent.all()
                                for parent in bud_parent:
                                    parent_uid = parent.uid
                                    parent_serialized = await parent.without_relations_serialize()
                                    if parent_uid not in buds_data:
                                        buds_data[parent_uid] = {
                                            'parent': parent_serialized,
                                            'commonAlbumsCount': 0,
                                            'commonAlbums': []
                                        }
                                    buds_data[parent_uid]['commonAlbumsCount'] += common_albums_count
                                    buds_data[parent_uid]['commonAlbums'].extend([await album.serialize() for album in common_albums])

                except Exception as e:
                    logger.error(f'Error processing bud: uid={bud_uid} - {e}', exc_info=True)
        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        buds_data_list = [
            {
                'bud': data['parent'],
                'commonAlbumsCount': data['commonAlbumsCount'],
                'commonAlbums': data['commonAlbums']
            }
            for data in buds_data.values()
        ]

        return buds_data_list, total_common_albums_count