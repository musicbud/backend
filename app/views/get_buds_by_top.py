from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.user import User
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')


class GetBudsBaseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    attribute_name = None

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(GetBudsBaseView, self).dispatch(*args, **kwargs)

    async def post(self, request):
        if not self.attribute_name:
            return JsonResponse({'error': 'Attribute name not specified'}, status=500)

        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            account_ids = [account.uid for account in user_node.associated_accounts.values() if account]
            unique_buds = set()

            items = await self._fetch_items(user_node)
            logger.debug(f'Fetched items: {items}')

            for item in items:
                if hasattr(item, 'users'):
                    item_users = await item.users.exclude(uid__in=account_ids).all()
                    unique_buds.update(user.uid for user in item_users if hasattr(user, 'uid'))

            logger.debug(f'Found {len(unique_buds)} unique buds for {self.attribute_name}.')

            buds_data = await self._fetch_buds_data(unique_buds)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by {self.attribute_name} for user: uid={user_node.uid}, total buds fetched: {len(unique_buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsBaseView: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def _fetch_items(self, user_node):
        items = []
        for account in user_node.associated_accounts.values():
            if account:
                if hasattr(account, self.attribute_name):
                    account_items = await getattr(account, self.attribute_name).all()
                    items.extend(account_items)
                else:
                    logger.warning(f'Account {account.uid} does not have {self.attribute_name} attribute.')
        return items

    async def _fetch_buds_data(self, unique_buds):
        buds_data = []

        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if not bud:
                    logger.warning(f'Bud not found: uid={bud_uid}')
                    continue

                bud_parent = await bud.parent.all()
                parent_serialized = await self._serialize_parent(bud_parent)

                buds_data.append({'bud': parent_serialized})

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        logger.debug(f'Prepared buds data list with {len(buds_data)} entries.')
        return buds_data

    async def _serialize_parent(self, bud_parent):
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data


class GetBudsByTopArtists(GetBudsBaseView):
    attribute_name = 'top_artists'


class GetBudsByTopTracks(GetBudsBaseView):
    attribute_name = 'top_tracks'


class GetBudsByTopGenres(GetBudsBaseView):
    attribute_name = 'top_genres'

class GetBudsByTopAnime(GetBudsBaseView):
    attribute_name = 'top_anime'

class GetBudsByTopManga(GetBudsBaseView):
    attribute_name = 'top_manga'
