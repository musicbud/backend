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

            # Prepare response structure for the bud profile
            response_data = {
                'data': {
                    'bud': await bud_node.without_relations_serialize(),  # Serialize the bud's profile without relations
                }
            }

            logger.info('Successfully fetched bud profile data for user=%s, bud_id=%s', user.uid, bud_id)
            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f'Error fetching bud profile: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)