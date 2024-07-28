from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..db_models.User import User
from ..db_models.Parent_User import ParentUser

from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination
import logging

logger = logging.getLogger('app')

class get_bud_profile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_bud_profile, self).dispatch(*args, **kwargs)
    
    async def post(self, request):
        try:
            user = request.user
            bud_id = request.data.get('bud_id')

            if not bud_id:
                return JsonResponse({'error': 'Bud ID not provided'}, status=400)

            bud_node = await ParentUser.nodes.get_or_none(uid=bud_id)

            if user is None or bud_node is None:
                logger.warning(f'User or bud not found: user={user}, bud_id={bud_id}')
                return JsonResponse({'error': 'User or bud not found'}, status=404)

            # Initialize dictionaries to collect likes
            user_likes = {}
            bud_likes = {}

            for account in user.associated_accounts.values():
                if account is not None and hasattr(account, 'get_likes'):
                    account_likes = await account.get_likes() or {}
                    for key, value in account_likes.items():
                        if key not in user_likes:
                            user_likes[key] = []
                        user_likes[key].extend(value)

            # Fetch likes from associated accounts for the bud
            accounts = await bud_node.associated_accounts()
            
            for account in accounts.values():
                if account is not None and hasattr(account, 'get_likes'):
                    account_likes = await account.get_likes() or {}
                    for key, value in account_likes.items():
                        if key not in bud_likes:
                            bud_likes[key] = []
                        bud_likes[key].extend(value)

            if not user_likes or not bud_likes:
                logger.warning('User likes or bud likes returned empty.')
                return JsonResponse({'error': 'No likes found for user or bud.'}, status=404)

            # Get common items for different categories
            common_artists = user.get_common_items(bud_likes.get('likes_artists', []), user_likes.get('likes_artists', []))
            common_tracks = user.get_common_items(bud_likes.get('likes_tracks', []), user_likes.get('likes_tracks', []))
            common_genres = user.get_common_items(bud_likes.get('likes_genres', []), user_likes.get('likes_genres', []))
            common_albums = user.get_common_items(bud_likes.get('likes_albums', []), user_likes.get('likes_albums', []))
            common_played_tracks = user.get_common_items(bud_likes.get('played_tracks', []), user_likes.get('played_tracks', []))

            async def serialize_common_items(common_items):
                serialized_items = {}
                for category, items in common_items.items():
                    serialized_items[category] = [await item.serialize() if hasattr(item, 'serialize') else item for item in items]
                return serialized_items

            # Serialize the common items to ensure they are JSON serializable
            serialized_common_items = await serialize_common_items({
                'common_artists': common_artists,
                'common_tracks': common_tracks,
                'common_genres': common_genres,
                'common_albums': common_albums,
                'common_played_tracks': common_played_tracks,
            })

            # Prepare response structure for the desired format
            response_data = {
                'data': {
                    'bud': await bud_node.serialize(),
                    'common_artists': serialized_common_items.get('common_artists', []),
                    'common_tracks': serialized_common_items.get('common_tracks', []),
                    'common_genres': serialized_common_items.get('common_genres', []),
                    'common_albums': serialized_common_items.get('common_albums', []),
                    'common_played_tracks': serialized_common_items.get('common_played_tracks', []),


                }
            }

            logger.info('Successfully fetched bud profile data for user=%s, bud_id=%s', user.uid, bud_id)
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'Error fetching bud profile: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
