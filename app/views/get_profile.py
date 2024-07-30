from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class GetItemsMixin(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    item_type = None
    item_attribute = None

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            items = []
            for account in user_node.associated_accounts.values():
                if account:
                    items_method = getattr(account, self.item_attribute, None)
                    if items_method:
                        account_items = await items_method.all()
                        items.extend(account_items)

            serialized_items = [await item.serialize() for item in items if hasattr(item, 'serialize')]

            paginator = StandardResultsSetPagination()
            paginated_items = paginator.paginate_queryset(serialized_items, request)

            paginated_response = paginator.get_paginated_response(paginated_items)
            paginated_response.update({
                'message': f'Fetched {self.item_type.replace("_", " ")} successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched {self.item_type.replace("_", " ")} for user: uid={user_node.uid}')
            return JsonResponse(paginated_response, safe=False)

        except Exception as e:
            logger.error(f'Error fetching {self.item_type}: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

class get_top_artists(GetItemsMixin):
    item_type = 'top_artists'
    item_attribute = 'top_artists'

class get_top_tracks(GetItemsMixin):
    item_type = 'top_tracks'
    item_attribute = 'top_tracks'

class get_top_genres(GetItemsMixin):
    item_type = 'top_genres'
    item_attribute = 'top_genres'

class get_liked_tracks(GetItemsMixin):
    item_type = 'liked_tracks'
    item_attribute = 'likes_tracks'

class get_liked_artists(GetItemsMixin):
    item_type = 'liked_artists'
    item_attribute = 'likes_artists'

class get_liked_genres(GetItemsMixin):
    item_type = 'liked_genres'
    item_attribute = 'likes_genres'

class get_liked_albums(GetItemsMixin):
    item_type = 'liked_albums'
    item_attribute = 'liked_albums'

class get_played_tracks(GetItemsMixin):
    item_type = 'played_tracks'
    item_attribute = 'played_tracks'
