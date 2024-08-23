from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..middlewares.custom_token_auth import CustomTokenAuthentication

import logging
logger = logging.getLogger('app')  # Use 'app' for consistency

class GetMyProfile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    async def post(self, request):
        try:
            parent_user = request.parent_user
            
            # Await the serialize method to get the actual user profile data
            user_profile = await parent_user.without_relations_serialize()

            # Create the response without pagination
            response = {
                'profile': user_profile,
                'message': 'Fetched Profile Successfully.',
                'code': 200,
                'successful': True,
            }

            return JsonResponse(response)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error fetching user profile: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
