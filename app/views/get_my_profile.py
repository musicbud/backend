from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class GetMyProfile(APIView):
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    async def post(self, request):
        try:
            parent_user = await request.user
            if not parent_user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fetch user profile data
            profile_data = {
                'username': parent_user.username,
                'email': parent_user.email,
                # Add other profile fields as needed
            }

            return Response(profile_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
