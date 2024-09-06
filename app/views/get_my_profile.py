from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from rest_framework.permissions import IsAuthenticated
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GetMyProfile(APIView):
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    async def post(self, request):
        try:
            parent_user = request.parent_user
            if not parent_user:
                logger.warning('User not found')
                return JsonResponse({'error': 'User not found'}, status=404)

            return JsonResponse(await parent_user.serialize(), status=200)
        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
