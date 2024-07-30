from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from app.services.ServiceSelector import get_service
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination
from ..middlewares.ServiceTokenGetter import service_token_getter

import logging
logger = logging.getLogger('app')  # Use 'app' for consistency

class get_my_profile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    async def post(self, request):
        try:
            parent_user = request.parent_user
            
            # Await the serialize method to get the actual user profile data
            user_profile = await parent_user.without_relations_serialize()

            # Paginate the profile data
            paginator = StandardResultsSetPagination()
            paginated_profile_data = paginator.paginate_queryset([user_profile], request)

            # Create the paginated response
            paginated_response = paginator.get_paginated_response(paginated_profile_data)
            paginated_response.update({
                'message': 'Fetched Profile Successfully.',
                'code': 200,
                'successful': True,
            })

            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f"Error fetching user profile: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
